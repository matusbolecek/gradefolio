import streamlit as st
import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv('token.env')

st.set_page_config(
    page_title="Gradefolio",
    page_icon="👋",
)

st.write("# Welcome to Gradefolio! 👋")

# I will put a readme here probably