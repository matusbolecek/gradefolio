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
client = OpenAI()

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
            database_path = f'groups/{group_name}.db'

            if os.path.isfile(database_path):
                results = dbman.search(idx, database_path, "id")
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
                prompt = open('prompts/summary.txt', 'r').read()

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
                    tex_filename = 'temp.tex'
                    shutil.copyfile('template.tex', tex_filename)

                    with open(tex_filename, "a") as tex_file:
                        tex_file.write(ai_output)
                        tex_file.write('\end{document}')

                    pdf, log, _ = PDFLaTeX.from_texfile(tex_filename).create_pdf()
                    pdf_filename = f'exports/{group_name}/{idx}_{name.replace(" ", "-")}.pdf'
                    Path(Path(pdf_filename).parent).mkdir(parents=True, exist_ok=True) # Make sure the output folder exists
                    
                    with open(pdf_filename, 'wb') as f:
                        f.write(pdf)
                    
                    os.remove('temp.tex')
                    progress += step
                    progress_placeholder.progress(progress, text=progressbar_caption)

            else:
                st.error(f'A database error occurred - the database *{group_name}.db* could not be found') # this should not happen

def write_stat(count):
    stat_path = 'local/daily.parquet'
    date_stamp = datetime.today().strftime('%Y-%m-%d')

    if os.path.isfile(stat_path):
        df = pd.read_parquet(stat_path)
        
        mask = df['date'] == date_stamp
        if mask.any():
            df.loc[mask, 'count'] += count
        else:
            df = df.append({'date': date_stamp, 'count': count}, ignore_index=True)
        
    else:
        d = {'date': date_stamp, 'count': count}
        df = pd.DataFrame(data=d)
    
    df.to_parquet(stat_path)
    return

st.write("# Generator")

# Group selector
groups = []
files = os.listdir('groups')
for file in files:
    if Path(file).suffix == '.csv':
        groups.append(Path(file).stem)
group_name = st.selectbox('Class', groups)

if group_name:
    df = pd.read_csv(f'groups/{group_name}.csv')
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

    if st.button("Submit"):
        selected = edited_df[edited_df['generate'] == True]
        if not selected.empty:
            to_process = [(idx, row['Students']) for idx, row in selected.iterrows()]
            generate(to_process, group_name) # temp
        else:
            st.info("No students selected.")

    # Download section
    st.write("### Download PDFs")

    for idx, row in df.iterrows():
        name = str(row['Students']).replace(' ', '-')
        pdf_path = f"exports/{group_name}/{idx}_{name}.pdf"

        col1, col2 = st.columns([4, 1])
        col1.write(name)

        if os.path.exists(pdf_path):
            with open(pdf_path, "rb") as f:
                pdf_data = f.read()
            col2.download_button(
                label="Download",
                data=pdf_data,
                file_name=f"{group_name}_{name}.pdf",
                mime="application/pdf",
                key=f"{group_name}_{name}"
            )
        else:
            col2.button(":x: Not created", key = name, disabled = True)
