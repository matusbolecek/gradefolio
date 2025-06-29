import streamlit as st
import os
from pathlib import Path
from openai import OpenAI
import database_manager as dbman

api_key = os.getenv('OPENAI_API_KEY')
client = OpenAI()
client.api_key = os.getenv("OPENAI_API_KEY")

@st.dialog("Update succesful") # This has to be fixed
def successful():
    st.write(f"Inputs have succesfully been added to the database")
    if st.button("Submit"):
        st.session_state['processed_text'] = None
        st.rerun()

if 'processed_text' not in st.session_state:
    st.session_state['processed_text'] = None

if st.session_state['processed_text'] == None:
    st.write("# Add an entry")

    groups = []
    files = os.listdir('groups')
    for file in files:
        if Path(file).suffix == '.csv':
            groups.append(Path(file).stem)

    group_name = st.selectbox('Class', groups)

    if group_name:
        st.subheader('Create an input')
        choice = st.selectbox('Input type', ['Report', 'Exam', 'Summary', 'Self'])

        audio_value = st.audio_input("Record a voice message")

        process_button = st.button('Process audio', disabled = not audio_value)
        if process_button:
            transcript = client.audio.transcriptions.create(
            model="whisper-1",
            file = audio_value
            )

            prompt = open(f'prompts/{choice.lower()}.txt', 'r').read()

            response = client.responses.create(
                model="gpt-4.1",
                input = prompt + transcript.text
            )

            st.session_state['processed_text'] = [group_name, choice, response.output_text]
            st.rerun()
else:
    st.header('Processed data:')
    st.subheader(f'Class: {st.session_state["processed_text"][0]}')

    write_out = str('')
    for line in (list(iter(st.session_state['processed_text'][2].splitlines()))):
        num, comment = line.split('-:-')
        write_out += f'Student {num} - {comment}\n'
    st.write(write_out)

    save_to_db = st.button('Save to database')
    if save_to_db:
        db_path = f'groups/{st.session_state["processed_text"][0]}.db'

        for line in (list(iter(st.session_state['processed_text'][2].splitlines()))):
            num, comment = line.split('-:-')
            dbman.add(str(num), st.session_state['processed_text'][1], comment, db_path)
            successful()

    restart = st.button('Restart')
    if restart:
        st.session_state['processed_text'] = None