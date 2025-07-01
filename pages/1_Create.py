import streamlit as st
import os
from pathlib import Path
from openai import OpenAI, OpenAIError
import pandas as pd

import database_manager as dbman

api_key = os.getenv('OPENAI_API_KEY')
client = OpenAI()

@st.dialog("Update succesful")
def successful(keyword: str):
    st.write(f"{keyword} inputs have succesfully been added to the database")
    if st.button("Submit"):
        st.session_state['processed_text'] = None
        st.rerun()

if 'error_msg' not in st.session_state: # init for later error handling
    st.session_state['error_msg'] = None

# Menu logic
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
        choice = st.selectbox('Input type', ['Report', 'Exam', 'Final', 'Self'])

        audio_value = st.audio_input("Record a voice message")
        process_button = st.button('Process audio', disabled = not audio_value)
        st.dataframe(pd.read_csv(f'groups/{group_name}.csv'))

        if process_button:
            with st.sidebar.status('Processing...'):
                st.write('Transcribing audio...')
                try:
                    transcript = client.audio.transcriptions.create(
                    model="whisper-1",
                    file = audio_value
                    )
                except OpenAIError as e:
                    st.error(f'Error: {e}')
                else:
                    st.write('Processing text...')
                    prompt = open(f'prompts/{choice.lower()}.txt', 'r').read()
                    try:
                        response = client.responses.create(
                            model="gpt-4.1",
                            input = prompt + transcript.text
                        )
                    except OpenAIError as e:
                        st.error(f'Error: {e}')
                    else:
                        try:
                            for line in (response.output_text.splitlines()):
                                num, comment = line.split('-:-')
                        except:
                            st.session_state['error_msg'] = (f'An error occurred - Please try again. The AI output is *{response.output_text}*')
                            st.rerun()
                        else:
                            st.session_state['processed_text'] = [group_name, choice, response.output_text]
                            st.write('Done')
                            
                            st.session_state['error_msg'] = None
                            st.rerun()

        if st.session_state['error_msg'] != None:
            st.error(st.session_state['error_msg'])
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
        csv_path = f'groups/{st.session_state["processed_text"][0]}.csv'
        df = pd.read_csv(csv_path)

        correct_inputs, wrong_inputs = 0, 0
        for line in (list(iter(st.session_state['processed_text'][2].splitlines()))):       
            num, comment = line.split('-:-')
            try:
                num = int(num) # Check if the num is in integer form
                dbman.add(str(num), st.session_state['processed_text'][1].upper(), comment, db_path) # Add entry into db
            except ValueError:
                st.session_state['error_msg'] = ('The input was processed incorrectly. Try again') # These do not show
                wrong_inputs += 1
            except:
                st.session_state['error_msg'] = ('An error occured while saving to the database')
                wrong_inputs += 1
            else:
                df.loc[int(num), f"{st.session_state['processed_text'][1]}s"] += 1 # Entry counter
                correct_inputs += 1
        
        if st.session_state['error_msg'] != None:
            st.error(st.session_state['error_msg'])
        
        if correct_inputs > 0:
            df['Sum'] = df.sum(axis=1, numeric_only=True)
            df.to_csv(csv_path, index=False)

            if wrong_inputs == 0:
                successful('All')
            else:
                successful(f'{correct_inputs} / {correct_inputs + wrong_inputs}')
        else:
            st.error('No correct entries were added to the database!')

    restart = st.button('Restart')
    if restart:
        st.session_state['processed_text'] = None