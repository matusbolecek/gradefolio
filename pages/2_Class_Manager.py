import streamlit as st
import os
from pathlib import Path
import pandas as pd
import time
import shutil

import database_manager as dbman

def go_back(): # Back button
    st.session_state['homescreen'] = True
    st.session_state['modify_mode'] = False
    st.session_state['add_mode'] = False
    st.rerun()

def create_group(names: list):
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

def move_all(group_name: str, folder: str):
    move_path = Path('local') / folder / f'{group_name}-{int(time.time())}'
    move_path.mkdir(parents=True, exist_ok=True)

    # Exports
    src_path = Path('exports') / group_name
    if src_path.exists():
        exports_dest = move_path / 'exports'
        exports_dest.mkdir(parents=True, exist_ok=True)
        
        for file_path in src_path.iterdir():
            if file_path.is_file():
                shutil.move(str(file_path), str(exports_dest))
        
        # Remove empty directory if it exists
        if src_path.exists() and not any(src_path.iterdir()):
            src_path.rmdir()

    # .csv and .db
    csv_path = Path('groups') / f'{group_name}.csv'
    db_path = Path('groups') / f'{group_name}.db'
    
    if csv_path.exists():
        shutil.move(str(csv_path), str(move_path))
    if db_path.exists():
        shutil.move(str(db_path), str(move_path))

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
            groups_dir = Path('groups')
            groups_dir.mkdir(exist_ok=True)
            csv_path = groups_dir / f'{new_name}.csv'
            if not csv_path.exists():
                st.session_state['temp_df'].to_csv(csv_path, index=False)
                st.success(f'Group "{new_name}" saved successfully!', icon="✅")
            else:
                st.error(f'Group "{new_name}" already exists')
    
    elif method == 'Cloning an existing group': # Cloning
        group_list = []
        groups_dir = Path('groups')
        if groups_dir.exists():
            for file_path in groups_dir.glob('*.csv'):
                group_list.append(file_path.stem)
        
        to_clone = st.selectbox('Select the group to clone', group_list)

        if to_clone:
            clone_csv_path = groups_dir / f'{to_clone}.csv'
            st.dataframe(pd.read_csv(clone_csv_path))
            confirm_clone = st.button('Clone this group')
            if confirm_clone:
                groups_dir.mkdir(exist_ok=True)
                csv_path = groups_dir / f'{new_name}.csv'
                if not csv_path.exists():
                    clone_df = pd.read_csv(clone_csv_path)
                    create_group(clone_df['Students'].tolist()).to_csv(csv_path, index=False)
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
                groups_dir = Path('groups')
                groups_dir.mkdir(exist_ok=True)
                csv_path = groups_dir / f'{new_name}.csv'
                if not csv_path.exists():
                    new_df.to_csv(csv_path, index=False)
                    st.success(f'Group "{new_name}" saved successfully!', icon="✅")                
                else:
                    st.error(f'Group "{new_name}" already exists')

# Modify mode
if st.session_state['modify_mode']:
    back_button = st.button('Go back')
    if back_button:
        go_back()
    
    # Read groups:
    groups = []
    groups_dir = Path('groups')
    if groups_dir.exists():
        for file_path in groups_dir.glob('*.csv'):
            groups.append(file_path.stem)

    group_name = st.selectbox('Class', groups)

    if group_name:
        action = st.selectbox('What to do with the group?', ['Edit', 'Archive', 'Delete'])
        csv_path = groups_dir / f'{group_name}.csv'

        if action == 'Edit':
            table = st.data_editor(pd.read_csv(csv_path), disabled = ("Reports", "Exams", "Finals", "Selfs", "Sum"))
            if st.button('Save changes'):
                table.to_csv(csv_path, index=False)
    
        elif action == 'Archive' or action == 'Delete':
            table = st.dataframe(pd.read_csv(csv_path))
            
            export_dir = Path('exports') / group_name
            if export_dir.exists():
                export_count = len(list(export_dir.glob('*')))
            else:
                export_count = 0
                
            st.write(f'Exported report count: {export_count}' if export_count > 0 else 'No exports from this group have been generated')
    
            user_sure = st.toggle(f'I am sure I want to {action.lower()} the group {group_name}')
            proceed_button = st.button('Proceed', disabled = not user_sure)
            if proceed_button:
                move_all(group_name, action.lower())
                st.rerun()

    else:
        st.info('No groups to modify!')