# 🎓 Gradefolio: LLM-Powered Student Portfolio & Assessment Generator

![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)
![OpenAI](https://img.shields.io/badge/OpenAI-Whisper%20%7C%20GPT--4o-412991.svg)
![Streamlit](https://img.shields.io/badge/Streamlit-Framework-FF4B4B.svg)

**Gradefolio** is an educational tool created as a part of my [2025 SOČ Competition entry](https://matusbolecek.com/#expand-soc-ai). It was built mainly as a proof of concept, but delivers a fully working system. Being open source, it can be easily adjusted and extended to one's needs

## The Problem & The Solution
**The Problem:** Traditional grading (numeric marks) often fails to provide valuable feedback for students. On the other hand, writing detailed verbal assessments for dozens of students is incredibly time-consuming as well as hard to keep up with over a longer time period 

**The Solution:** Gradefolio allows teachers to record quick voice memos after a class. The system automatically transcribes, analyzes, categorizes, and stores these events locally. At the end of the term, the system synthesizes the recorded data into a simple PDF report using an LLM. 

## System Architecture & Data Pipeline

Gradefolio operates on a modular data pipeline, processing unstructured audio into structured database entries, and finally into compiled documents.

1. **Audio Recording:** Teachers record quick voice notes via the Streamlit UI
2. **Transcription:** Audio is transcribed with high accuracy (including Slovak dialects) using [OpenAI's Whisper-1](https://openai.com/index/whisper/)
3. **Information Extraction (LLM):** The transcribed text is processed by an LLM model. Based on the event type (`Report`, `Exam`, `Final`, `Self-Evaluation`), the model extracts the important information, removes fluff, and formats the data as `STUDENT_ID-:-Observation`. Each of the event types has specialized instructions to maximize the model efficiency
4. **Local Database:** Data is logged into a local **SQLite** database and tracked via Pandas DataFrames/Parquet files. *Crucially, only Student IDs are sent to the LLMs during the extraction phase in order to keep the student data sent out free from exact personal identifiers*
5. **Synthesis & Calibration:** When generating reports, the system retrieves all historical entries for a student in a group and synthesizes them into a singular report using a master summary prompt
6. **Automated Typesetting:** The final text is injected into a `.tex` template and compiled into a styled PDF using `pdflatex`.

## Prompt Engineering
The core success of this tool relies on complex system prompts (`consts.py`) grounded in pedagogical research (as further explained in my thesis). Key prompt constraints include:

* **The 3:1 Ratio:** The LLM is instructed to maintain a 3:1 ratio of positive reinforcement to constructive criticism, adhering to modern humanistic psychology standards in education
* **Self-Evaluation Bias Calibration:** The `Self` prompt actively calibrates student inputs. It is designed to automatically identify and moderate biases.
* **Actionable Formatting:** The models are restricted from using subjective grading jargon ("poor," "excellent") and encouraged to to use descriptive, observable behaviors

## Tech Stack
* **Frontend:** Streamlit, Plotly (for activity heatmaps/trend visualization)
* **Backend:** Python, Pandas, SQLite3
* **AI Integration:** OpenAI API (Whisper-1, GPT-5.2)
* **Document Generation:** pdflatex 

## Installation & Setup

1. **Clone the repository:**
   ```sh
   git clone https://github.com/matusbolecek/Gradefolio.git
   cd Gradefolio
   ```

2. **Install dependencies:**
   ```sh
   pip install -r requirements.txt
   ```
   *Note: Ensure you have a LaTeX distribution (like TeX Live or MiKTeX) installed on your system to enable PDF generation.*

3. **Environment Variables:**
   Create a `token.env` file in the root directory and add your [OpenAI API key](https://platform.openai.com/home):
   ```env
   OPENAI_API_KEY=your_api_key_here
   ```

4. **Run the application:**
   ```sh
   streamlit run Home.py
   ```

## Author
This project was developed as the practical component of my research paper *"Generative Artificial Intelligence as a Tool for Modern Education"* 

**Matúš Boleček**
* Data Science Student @ Aarhus University
* [LinkedIn](https://linkedin.com/in/matus-bolecek) | [Portfolio Website](https://matusbolecek.com)
