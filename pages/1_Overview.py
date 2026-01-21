import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import re

st.set_page_config(
    page_title="Overview | Legal Analytics Dashboard",
    layout="wide"
)

st.title("Legal Analytics Dashboard - Overview")

@st.cache_data
def load_data():
    return pd.read_parquet("data/base_for_dashboard.parquet")

df = load_data()

st.sidebar.header("Filters")

min_year = int(df["year"].min())
max_year = int(df["year"].max())

year_range = st.sidebar.slider(
    "Select Year Range",
    min_year,
    max_year,
    (min_year, max_year)
)

filtered_df = df[
    (df["year"] >= year_range[0]) &
    (df["year"] <= year_range[1])
]

def extract_judges_from_clean(text):
    if not isinstance(text, str):
        return []

    match = re.search(
        r"Coram\s*:\s*(.*?)(?:Decision Date|Case No|\n|$)",
        text,
        flags=re.IGNORECASE | re.DOTALL
    )

    if not match:
        return []

    names = []
    for part in re.split(r",| and ", match.group(1)):
        part = part.strip()
        if 6 <= len(part) <= 60:
            names.append(part.title())

    return names

filtered_df["judges"] = filtered_df["clean_text"].apply(extract_judges_from_clean)

st.subheader("Dataset Summary")

c1, c2, c3 = st.columns(3)

with c1:
    st.metric("Total Cases", len(filtered_df))

with c2:
    st.metric(
        "Judges Identified",
        filtered_df.explode("judges")["judges"].nunique()
    )

with c3:
    st.metric(
        "Years Covered",
        f"{year_range[0]} - {year_range[1]}"
    )

st.subheader("Cases per Year")

cases_per_year = (
    filtered_df.groupby("year")
    .size()
    .reset_index(name="case_count")
)

fig, ax = plt.subplots()
ax.plot(cases_per_year["year"], cases_per_year["case_count"])
ax.set_xlabel("Year")
ax.set_ylabel("Number of Cases")

st.pyplot(fig)

st.subheader("Top Judges (Derived from Text)")

top_judges = (
    filtered_df
    .explode("judges")
    .dropna(subset=["judges"])
    .groupby("judges")
    .size()
    .reset_index(name="case_count")
    .sort_values("case_count", ascending=False)
    .head(15)
)

fig, ax = plt.subplots()
ax.barh(top_judges["judges"], top_judges["case_count"])
ax.invert_yaxis()
ax.set_xlabel("Number of Cases")

st.pyplot(fig)

st.subheader("Sample Cases")

st.dataframe(
    filtered_df[["year", "title", "court"]].head(25),
    use_container_width=True
)
