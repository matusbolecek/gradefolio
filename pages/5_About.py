import streamlit as st
import requests

st.set_page_config(page_title="About Gradefolio", page_icon="👋")

GITHUB_RAW_URL = (
    "https://raw.githubusercontent.com/matusbolecek/gradefolio/main/README.md"
)


@st.cache_data(ttl=3600)
def fetch_readme(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.text

    except requests.exceptions.RequestException as e:
        return None


readme_content = fetch_readme(GITHUB_RAW_URL)

if readme_content:
    st.markdown(readme_content, unsafe_allow_html=True)

else:
    st.write("# About Gradefolio 👋")
    # This should not happen if the repo is up normally - only in case of connection problems
    st.error("Could not load the README file. Please check your connection.")

