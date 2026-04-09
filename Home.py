import streamlit as st
from dotenv import load_dotenv
import plotly.express as px
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

load_dotenv("token.env")

st.set_page_config(page_title="Gradefolio Dashboard", page_icon="🎓", layout="centered")


@st.cache_data(ttl=60)
def find_most_frequent_group(window_minutes=20) -> Optional[str]:
    file_path = Path("local") / "group_freq.parquet"
    if not Path(file_path).exists():
        return None

    df = pd.read_parquet(file_path)
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    current_time = datetime.now()

    start_time = current_time - timedelta(minutes=window_minutes)
    end_time = current_time + timedelta(minutes=window_minutes)

    mask = (df["timestamp"] >= start_time) & (df["timestamp"] <= end_time)
    filtered_df = df[mask]

    if len(filtered_df) == 0:
        return None

    return str(filtered_df["group"].value_counts().index[0])


@st.cache_data(ttl=10)
def get_global_stats():
    total_classes = 0
    total_students = 0
    total_entries = 0

    groups_dir = Path("groups")
    if groups_dir.exists():
        for file_path in groups_dir.glob("*.csv"):
            total_classes += 1

            try:
                df = pd.read_csv(file_path)
                total_students += len(df)

                if "Sum" in df.columns:
                    total_entries += df["Sum"].sum()

            except Exception:
                pass

    return total_classes, total_students, int(total_entries)


st.title("Gradefolio Dashboard")
st.markdown("Welcome back! Here is an overview of your teaching and grading activity.")

most_frequent = find_most_frequent_group()
if most_frequent != None:
    st.session_state["selected_group"] = most_frequent
    st.info(
        f"**Quick Resume:** You recently worked on **{most_frequent}**. Head over to [Create](Create) to add more entries."
    )

classes, students, entries = get_global_stats()
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Active Classes", classes)

with col2:
    st.metric("Total Students", students)

with col3:
    st.metric("Portfolio Entries", entries)

st.divider()

st.subheader("Quick Actions")
col_a, col_b, col_c = st.columns(3)

with col_a:
    if st.button("Add New Entry", use_container_width=True):
        st.switch_page("pages/1_Create.py")

with col_b:
    if st.button("Generate PDFs", use_container_width=True):
        st.switch_page("pages/3_Generator.py")

with col_c:
    if st.button("Manage Classes", use_container_width=True):
        st.switch_page("pages/2_Class_Manager.py")

st.divider()

st.subheader("Activity (Last 30 Days)")

end_date = datetime.now().date()
start_date = end_date - timedelta(days=29)
all_dates = pd.date_range(start=start_date, end=end_date, freq="D")
complete_df = pd.DataFrame({"date": all_dates, "count": 0})
complete_df["date"] = complete_df["date"].dt.date

try:
    df = pd.read_parquet(Path("local") / "daily.parquet")
    df["date"] = pd.to_datetime(df["date"]).dt.date

    complete_df = complete_df.set_index("date")
    df = df.set_index("date")
    complete_df.update(df)
    complete_df = complete_df.reset_index()

except FileNotFoundError:
    pass

fig = px.bar(
    complete_df,
    x="date",
    y="count",
    labels={"date": "", "count": "Entries"},
)

# Styling for dark/light mode
theme_color = "#1f6feb" if st.context.theme.type == "dark" else "#2ea043"

fig.update_traces(marker_color=theme_color, marker_line_width=0, opacity=0.8)
fig.update_layout(
    plot_bgcolor="rgba(0,0,0,0)",
    paper_bgcolor="rgba(0,0,0,0)",
    margin=dict(l=0, r=0, t=10, b=0),
    xaxis=dict(showgrid=False, fixedrange=True),
    yaxis=dict(showgrid=True, gridcolor="rgba(128, 128, 128, 0.2)", fixedrange=True),
    height=250,
    hovermode="x unified",
)

st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
