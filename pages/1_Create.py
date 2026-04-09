import streamlit as st
from pathlib import Path
from openai import OpenAIError
import pandas as pd
from datetime import datetime

import database_manager as dbman
from consts import Prompts
from utils import Model, NoApiKey

# Init openai
try:
    model = Model()
    client = model.client

except (NoApiKey, OpenAIError) as e:
    st.write(f"An error has occured: {e}")
    st.stop()


@st.dialog("Update succesful")
def successful(keyword: str):
    st.write(f"{keyword} inputs have succesfully been added to the database")
    if st.button("Submit"):
        st.session_state["processed_text"] = None
        st.rerun()


def write_stat(count: int) -> None:
    stat_path = Path("local") / "daily.parquet"
    date_stamp = datetime.today().strftime("%Y-%m-%d")

    if stat_path.exists():
        df = pd.read_parquet(stat_path)

        mask = df["date"] == date_stamp
        if mask.any():
            df.loc[mask, "count"] += count
        else:
            df = pd.concat(
                [df, pd.DataFrame([{"date": date_stamp, "count": count}])],
                ignore_index=True,
            )

    else:
        df = pd.DataFrame([{"date": date_stamp, "count": count}])

    # Ensure parent dir exists
    stat_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(stat_path)


def save_group_entry(group_name: str) -> None:
    file_path = Path("local") / "group_freq.parquet"
    timestamp = datetime.now()

    new_entry = pd.DataFrame({"timestamp": [timestamp], "group": [group_name]})

    if Path(file_path).exists():
        existing_df = pd.read_parquet(file_path)
        df = pd.concat([existing_df, new_entry], ignore_index=True)
    else:
        df = new_entry

    df.to_parquet(file_path, index=False)


if "selected_group" not in st.session_state:
    st.session_state["selected_group"] = None

if "error_msg" not in st.session_state:  # init for later error handling
    st.session_state["error_msg"] = None

# Menu logic
if "processed_text" not in st.session_state:
    st.session_state["processed_text"] = None

if st.session_state["processed_text"] == None:
    st.write("# Add an entry")

    groups = []
    groups_dir = Path("groups")
    if groups_dir.exists():
        for file_path in groups_dir.glob("*.csv"):
            groups.append(file_path.stem)

    group_index = (
        0
        if st.session_state["selected_group"] == None
        else groups.index(st.session_state["selected_group"])
    )
    group_name = st.selectbox("Class", groups, index=group_index)

    if group_name:
        st.subheader("Create an input")
        prompter = Prompts()
        choice = st.selectbox("Input type", prompter.types)

        audio_value = st.audio_input("Record a voice message")
        process_button = st.button("Process audio", disabled=not audio_value)

        csv_path = groups_dir / f"{group_name}.csv"
        st.dataframe(pd.read_csv(csv_path))

        if process_button:
            with st.sidebar.status("Processing..."):
                st.write("Transcribing audio...")
                try:
                    transcript = client.audio.transcriptions.create(
                        model="whisper-1", file=audio_value
                    )
                except OpenAIError as e:
                    st.error(f"Error: {e}")
                else:
                    st.write("Processing text...")
                    prompt = prompter.get_prompt(choice)

                    try:
                        response = client.responses.create(
                            model=model.version, input=prompt + transcript.text
                        )

                    except OpenAIError as e:
                        st.error(f"Error: {e}")

                    else:
                        try:
                            for line in response.output_text.splitlines():
                                num, comment = line.split("-:-")

                        except:
                            st.session_state["error_msg"] = (
                                f"An error occurred - Please try again. The AI output is *{response.output_text}*"
                            )
                            st.rerun()

                        else:
                            st.session_state["processed_text"] = [
                                group_name,
                                choice,
                                response.output_text,
                            ]
                            st.write("Done")

                            st.session_state["error_msg"] = None
                            st.rerun()

        if st.session_state["error_msg"] != None:
            st.error(st.session_state["error_msg"])
else:
    st.header("Processed data:")
    st.subheader(f'Class: {st.session_state["processed_text"][0]}')

    write_out = str("")
    for line in list(iter(st.session_state["processed_text"][2].splitlines())):
        num, comment = line.split("-:-")
        write_out += f"Student {num} - {comment}\n"
    st.write(write_out)

    save_to_db = st.button("Save to database")
    if save_to_db:
        groups_dir = Path("groups")
        db_path = groups_dir / f'{st.session_state["processed_text"][0]}.db'
        csv_path = groups_dir / f'{st.session_state["processed_text"][0]}.csv'
        df = pd.read_csv(csv_path)

        correct_inputs, wrong_inputs = 0, 0
        col_name = f"{st.session_state['processed_text'][1]}s"

        if col_name not in df.columns:
            st.session_state["error_msg"] = f"Column '{col_name}' not found in database"
            st.error(st.session_state["error_msg"])
        else:
            db = dbman.DatabaseManager(str(db_path))

            for line in st.session_state["processed_text"][2].splitlines():
                if not line.strip():  # Skip empty line
                    continue

                try:
                    if "-:-" not in line:
                        raise ValueError("Invalid line format")

                    num_str, comment = line.split(
                        "-:-", 1
                    )  # Split only on first occurrence
                    num = int(num_str.strip())
                    comment = comment.strip()

                    if not (0 <= num < len(df)):
                        raise IndexError(f"Student number {num} out of range")

                    db.add(
                        str(num),
                        st.session_state["processed_text"][1].upper(),
                        comment,
                    )

                    df.at[num, col_name] += 1
                    correct_inputs += 1

                except ValueError as e:
                    st.session_state["error_msg"] = (
                        f'Invalid input format in line: "{line[:50]}..."'
                    )
                    wrong_inputs += 1

                except IndexError as e:
                    st.session_state["error_msg"] = f"Student number out of range: {e}"
                    wrong_inputs += 1

                except Exception as e:
                    st.session_state["error_msg"] = f"Database error: {str(e)}"
                    wrong_inputs += 1

            # Final error msg in case of errors
            if st.session_state["error_msg"] and wrong_inputs > 0:
                st.error(st.session_state["error_msg"])

            if correct_inputs > 0:
                df["Sum"] = df.sum(axis=1, numeric_only=True)
                df.to_csv(csv_path, index=False)
                save_group_entry(
                    st.session_state["processed_text"][0]
                )  # Write timestamp with group
                write_stat(correct_inputs)

                if wrong_inputs == 0:
                    successful("All")
                else:
                    successful(f"{correct_inputs} / {correct_inputs + wrong_inputs}")
            else:
                st.error("No correct entries were added to the database!")

    restart = st.button("Restart")
    if restart:
        st.session_state["processed_text"] = None
