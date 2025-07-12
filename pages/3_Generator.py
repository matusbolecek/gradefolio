import streamlit as st
import os
from pathlib import Path
import pandas as pd
from pdflatex import PDFLaTeX
import shutil
from openai import OpenAI, OpenAIError
from datetime import datetime

import database_manager as dbman

api_key = os.getenv('OPENAI_API_KEY')
if not api_key:
    st.error("OpenAI API key not found. Please set the OPENAI_API_KEY environment variable.")
    st.stop()

try:
    client = OpenAI(api_key=api_key)
except OpenAIError as e:
    st.error(f"Failed to initialize OpenAI client: {e}")
    st.stop()

def generate(students: list, group_name: str):
    progressbar_caption = f'Processing {len(students)} file{"s" if len(students) != 1 else ""}'
    progress, step = 0.0, 1.0 / len(students)
    progress_placeholder = st.sidebar.empty()
    progress_placeholder.progress(progress, text=progressbar_caption)
    
    for sets in students:
        idx, name = sets[0], sets[1]
        with st.sidebar.status(f"Processing {name}"):
            
            # Retrieve entries from database
            st.write("Retrieving entries from the database")
            reports, exams, finals, selfs = [], [], [], []
            final_string = str('')
            database_path = Path('groups') / f'{group_name}.db'

            if database_path.exists():
                results = dbman.search(idx, str(database_path), "id")
                for a in results:
                    if a[1] == 'REPORT':
                        reports.append(a[2])
                    elif a[1] == 'EXAM':
                        exams.append(a[2])
                    elif a[1] == 'FINAL':
                        finals.append(a[2])
                    elif a[1] == 'SELF':
                        selfs.append(a[2])

                if len(reports) != 0:
                    final_string += 'Reports from classes:\n'
                    for x in reports:
                        final_string += f'{x}\n'
                if len(exams) != 0:
                    final_string += 'Exams:\n'
                    for x in exams:
                        final_string += f'{x}\n'
                if len(finals) != 0:
                    final_string += 'Final summaries:\n'
                    for x in finals:
                        final_string += f'{x}\n'
                if len(selfs) != 0:
                    final_string += 'Self evaluations:\n'
                    for x in selfs:
                        final_string += f'{x}\n'

                # Process with LLM
                st.write("Talking to AI")
                prompt_path = Path('prompts') / 'summary.txt'
                prompt = prompt_path.read_text(encoding = 'utf-8')

                try:
                    response = client.responses.create(
                        model="gpt-4.1",
                        input = prompt + final_string
                    )
                except OpenAIError as e:
                    st.error(f'Error: {e}')
                else:
                    ai_output = response.output_text.replace("**name**", name)

                    # Generate PDF
                    st.write("Generating the PDF")
                    tex_filename = Path('temp.tex')
                    template_path = Path('template.tex')
                    shutil.copyfile(template_path, tex_filename)

                    with tex_filename.open("a", encoding='utf-8') as tex_file:
                        tex_file.write(ai_output)
                        tex_file.write(r'\end{document}')

                    pdf, log, _ = PDFLaTeX.from_texfile(str(tex_filename)).create_pdf()
                    pdf_filename = Path('exports') / group_name / f'{idx}_{name.replace(" ", "-")}.pdf'
                    pdf_filename.parent.mkdir(parents=True, exist_ok=True)
                    
                    pdf_filename.write_bytes(pdf)
                    
                    tex_filename.unlink() # Remove temp.tex
                    progress += step
                    progress_placeholder.progress(progress, text=progressbar_caption)

            else:
                st.error(f'A database error occurred - the database *{group_name}.db* could not be found')

def write_stat(count):
    stat_path = Path('local') / 'daily.parquet'
    date_stamp = datetime.today().strftime('%Y-%m-%d')

    if stat_path.exists():
        df = pd.read_parquet(stat_path)
        
        mask = df['date'] == date_stamp
        if mask.any():
            df.loc[mask, 'count'] += count
        else:
            df = pd.concat([df, pd.DataFrame([{'date': date_stamp, 'count': count}])], ignore_index=True)
        
    else:
        d = {'date': date_stamp, 'count': count}
        df = pd.DataFrame(data=d)
    
    # Ensure parent dir exists
    stat_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(stat_path)
    return

st.write("# Generator")

# Group selector
groups = []
groups_dir = Path('groups')
if groups_dir.exists():
    for file_path in groups_dir.glob('*.csv'):
        groups.append(file_path.stem)
group_name = st.selectbox('Class', groups)

if group_name:
    csv_path = groups_dir / f'{group_name}.csv'
    df = pd.read_csv(csv_path)
    if 'generate' not in df.columns:
        df['generate'] = False

    st.write("### Students in Group")
    edited_df = st.data_editor(
        df,
        disabled = ("Students", "Reports", "Exams", "Finals", "Selfs", "Sum"),
        column_config={
            "generate": st.column_config.CheckboxColumn(
                "Generate?",
                default=False,
            )
        },
        use_container_width=True,
        key="student_editor"
    )

    # Check if file exists
    excluded = []
    exports_dir = Path('exports') / group_name
    for idx, row in edited_df[edited_df['generate'] == True].iterrows():
        filename = exports_dir / f'{idx}_{row["Students"].replace(" ", "-")}.pdf'
        if filename.exists():
            excluded.append((idx, row["Students"]))

    overwrite = st.checkbox('Overwrite existing outputs', disabled = not len(excluded) > 0)
    selected = edited_df[edited_df['generate'] == True]

    if st.button("Submit", disabled = selected.empty):
        to_process = [(idx, row["Students"]) for idx, row in selected.iterrows()]

        if not overwrite:
            to_process = [x for x in to_process if x not in excluded]

        if to_process:
            generate(to_process, group_name)
        else:
            st.info("No reports to process.")

    # Download section
    st.write("### Download PDFs")

    for idx, row in df.iterrows():
        name = str(row['Students']).replace(' ', '-')
        pdf_path = exports_dir / f"{idx}_{name}.pdf"

        col1, col2 = st.columns([4, 1])
        col1.write(name)

        if pdf_path.exists():
            pdf_data = pdf_path.read_bytes()
            col2.download_button(
                label="Download",
                data=pdf_data,
                file_name=f"{group_name}_{name}.pdf",
                mime="application/pdf",
                key=f"{group_name}_{name}"
            )
        
        else:
            col2.button(":x: Not created", key = name, disabled = True)