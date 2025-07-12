import streamlit as st
from dotenv import load_dotenv
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
import json
from typing import Optional

load_dotenv('token.env')

config_path = Path('local') / 'config.json'

if Path.exists(config_path):
    with open('config.json', 'r') as f:
        config = json.load(f)
else:
    config = False

st.set_page_config(
    page_title="Gradefolio",
    page_icon="👋",
)

def find_most_frequent_group(window_minutes=20) -> Optional[str]:
    file_path = Path('local') / 'group_freq.parquet'
    if not Path(file_path).exists():
        return None
    
    df = pd.read_parquet(file_path)

    # Convert timestamp column to datetime if needed
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    
    current_time = datetime.now()
    
    start_time = current_time - timedelta(minutes=window_minutes)
    end_time = current_time + timedelta(minutes=window_minutes)
    
    mask = (df['timestamp'] >= start_time) & (df['timestamp'] <= end_time)
    filtered_df = df[mask]
    
    if len(filtered_df) == 0:
        return None
        
    return str(filtered_df['group'].value_counts().index[0])

name_section = f', {config["name"]}' if config else ''
st.write(f"# Welcome to Gradefolio{name_section}! 👋")

most_frequent = find_most_frequent_group()

# Simple quick suggestion on homepage based on time
if most_frequent != None:
    st.session_state['selected_group'] = most_frequent
    st.divider()
    st.page_link("pages/1_Create.py", label=f"Want to add a quick entry for the group {most_frequent}")

# Heatmap of contribs
if st.context.theme.type == 'dark':
    colorscale = [[0, '#0d1117'], [0.1, '#161b22'], [0.3, '#21262d'], [0.5, '#1f6feb'], [0.7, '#58a6ff'], [1, '#79c0ff']]
    border_color = '#30363d'
else: # light
    colorscale = 'greens'
    border_color = '#e1e4e8'

end_date = datetime.now().date()
start_date = end_date - timedelta(days = 89)
all_dates = pd.date_range(start = start_date, end = end_date, freq = 'D')
complete_df = pd.DataFrame({'date': all_dates, 'count': 0})

try:
    df = pd.read_parquet(Path('local') / 'daily.parquet')
    df['date'] = pd.to_datetime(df['date']).dt.date
    complete_df['date'] = complete_df['date'].dt.date
    complete_df = complete_df.set_index('date')
    df = df.set_index('date')
    complete_df.update(df)
    complete_df = complete_df.reset_index()
except FileNotFoundError:
    pass # file does not exist - all fields will be zeroes

complete_df = complete_df.sort_values(by='date')

days_per_row = 30
rows = 3
total_cells = rows * days_per_row
current_length = len(complete_df)

if current_length < total_cells:
    padding_dates = pd.date_range(start=complete_df['date'].min() - timedelta(days = total_cells - current_length), periods = total_cells - current_length, freq='D')
    padding_df = pd.DataFrame({'date': padding_dates, 'count': 0})
    complete_df = pd.concat([padding_df, complete_df], ignore_index = True)

complete_df = complete_df.tail(total_cells)

z_matrix = np.array(complete_df['count'].values).reshape(rows, days_per_row)
dates_matrix = np.array(complete_df['date'].values).reshape(rows, days_per_row)

fig = go.Figure(data=go.Heatmap(
    z = z_matrix,
    colorscale = colorscale,
    showscale = True,
    hoverongaps = False,
    customdata = dates_matrix,
    hovertemplate = 'Date: %{customdata}<br>Count: %{z}<extra></extra>',
    xgap = 0.5,
    ygap = 0.5
))

fig.update_layout(
    title = 'Entries in the last 90 days',
    xaxis = dict(title = 'Days', showticklabels = False, showgrid = False),
    yaxis = dict(title = '', showticklabels = False, showgrid = False),
    height = 170,
    margin = dict(l = 20, r = 20, t = 40, b = 20),
    plot_bgcolor = border_color
)

st.plotly_chart(fig, use_container_width=True)