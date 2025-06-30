import streamlit as st
import os
from pathlib import Path
import pandas as pd

import database_manager as dbman

def go_back(): # Back button
    st.session_state['homescreen'] = True
    st.session_state['modify_mode'] = False
    st.session_state['add_mode'] = False
    st.rerun()

def create_group(names):
    data = {
        "Students": names,
        "Reports": [0] * len(names),
        "Exams": [0] * len(names),
        "Finals": [0] * len(names),
        "Selfs": [0] * len(names),  
    }
    df = pd.DataFrame(data)
    df['Sum'] = df.sum(axis=1, numeric_only=True)
    
    return df

# Session states init
if 'homescreen' not in st.session_state:
    st.session_state['homescreen'] = True
if 'add_mode' not in st.session_state:
    st.session_state['add_mode'] = False
if 'modify_mode' not in st.session_state:
    st.session_state['modify_mode'] = False
if 'temp_df' not in st.session_state:
    st.session_state['temp_df'] = None
if 'df_set' not in st.session_state:
    st.session_state['df_set'] = False

# Home screen
if st.session_state['homescreen']:
    if not st.session_state['modify_mode']:
        if st.button('Add group'):
            st.session_state['homescreen'] = False
            st.session_state['add_mode'] = True
            st.rerun()
    if not st.session_state['add_mode']:
        if st.button('Modify group'):
            st.session_state['homescreen'] = False
            st.session_state['modify_mode'] = True
            st.rerun()

# Add mode
if st.session_state['add_mode']:
    if st.button('Go back'):
        go_back()
    
    st.subheader('Adding a group')
    new_name = st.text_input('Name the group')
    method = st.selectbox('Method', ['Cloning an existing group', 'From .csv', 'Manually'])
    st.write(f"Selected method: {method}")
    
    if method == 'Manually': # Manual input
        names = st.text_input('Add the student names separated by a comma (ex. Peter, John, Mark...)')
        
        if st.button("Submit"):
            if new_name and names:
                new_name = new_name.strip().replace(' ', '-')
                student_names = [name.strip() for name in names.split(',') if name.strip()]
                st.session_state['temp_df'] = create_group(student_names)
                st.session_state['df_set'] = True
            else:
                st.warning('Not all fields have been filled out')
        
        if st.session_state['df_set'] == True:
            st.session_state['temp_df'] = st.data_editor(st.session_state['temp_df'], key="data_editor", disabled = ("Reports", "Exams", "Finals", "Selfs", "Sum"))

        # Save button
        if 'temp_df' in st.session_state and st.button('Save group'):
            os.makedirs('groups', exist_ok=True)
            csv_path = f'groups/{new_name}.csv'
            if not os.path.isfile(csv_path):
                st.session_state['temp_df'].to_csv(csv_path, index=False)
                st.success(f'Group "{new_name}" saved successfully!', icon="✅")
            else:
                st.error(f'Group "{new_name}" already exists')
    
    elif method == 'Cloning an existing group': # Cloning
        group_list = []
        files = os.listdir('groups')
        for file in files:
            if Path(file).suffix == '.csv':
                group_list.append(Path(file).stem)
        to_clone = st.selectbox('Select the group to clone', group_list)

        if to_clone:
            st.dataframe(pd.read_csv(f'groups/{to_clone}.csv'))
            confirm_clone = st.button('Clone this group')
            if confirm_clone:
                os.makedirs('groups', exist_ok=True)
                csv_path = f'groups/{new_name}.csv'
                if not os.path.isfile(csv_path):
                    create_group(pd.DataFrame(pd.read_csv(f'groups/{to_clone}.csv'))['Students'].tolist()).to_csv(csv_path, index=False)

                    st.success(f'Group "{new_name}" saved successfully!', icon="✅")                
                else:
                    st.error(f'Group "{new_name}" already exists')
    
    elif method == 'From .csv': # File upload
        uploaded_csv = st.file_uploader('Upload your .csv with', type = '.csv')
        no_headers = st.toggle('List with no headers')

        if uploaded_csv:
            if no_headers:
                df = pd.read_csv(uploaded_csv, header = None)
            else:
                df = pd.read_csv(uploaded_csv)   

            new_df = create_group(df.iloc[:, 0].tolist())
            st.dataframe(new_df)

            clone_button = st.button('Clone this database')
            if clone_button and new_name:
                os.makedirs('groups', exist_ok=True)
                csv_path = f'groups/{new_name}.csv'
                if not os.path.isfile(csv_path):
                    new_df.to_csv(csv_path, index=False)
                    st.success(f'Group "{new_name}" saved successfully!', icon="✅")                
                else:
                    st.error(f'Group "{new_name}" already exists')

# Modify mode
if st.session_state['modify_mode']:
    back_button = st.button('Go back')
    if back_button:
        go_back()
    st.write("Modify group functionality goes here...")