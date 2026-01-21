import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import re

st.set_page_config(
    page_title="Citation Analytics | Legal Analytics Dashboard",
    layout="wide"
)

st.title("Citation Analytics")

@st.cache_data
def load_data():
    return pd.read_parquet("data/base_for_dashboard.parquet")

df = load_data()

if "citation" not in df.columns:
    st.error("Citation column not found in dataset.")
    st.stop()

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

def split_citations(citation_value):
    if pd.isna(citation_value):
        return []

    if isinstance(citation_value, list):
        return citation_value

    text = str(citation_value)

    parts = re.split(r",|;", text)
    return [p.strip() for p in parts if len(p.strip()) > 3]

filtered_df["citation_list"] = filtered_df["citation"].apply(split_citations)

st.subheader("Citation Summary")

c1, c2, c3 = st.columns(3)

with c1:
    st.metric("Total Cases", len(filtered_df))

with c2:
    st.metric(
        "Unique Citations",
        filtered_df.explode("citation_list")["citation_list"].nunique()
    )

with c3:
    st.metric(
        "Years Covered",
        f"{year_range[0]} - {year_range[1]}"
    )

st.subheader("Most Frequent Citations")

top_citations = (
    filtered_df
    .explode("citation_list")
    .dropna(subset=["citation_list"])
    .groupby("citation_list")
    .size()
    .reset_index(name="case_count")
    .sort_values("case_count", ascending=False)
    .head(20)
)

fig, ax = plt.subplots()
ax.barh(top_citations["citation_list"], top_citations["case_count"])
ax.invert_yaxis()
ax.set_xlabel("Number of Cases")
ax.set_ylabel("Citation")

st.pyplot(fig)

st.subheader("Citation Trends Over Time")

selected_citation = st.selectbox(
    "Select a Citation",
    top_citations["citation_list"].tolist()
)

citation_df = filtered_df[
    filtered_df["citation_list"].apply(
        lambda lst: selected_citation in lst if isinstance(lst, list) else False
    )
]

trend = (
    citation_df.groupby("year")
    .size()
    .reset_index(name="case_count")
)

fig, ax = plt.subplots()
ax.plot(trend["year"], trend["case_count"])
ax.set_xlabel("Year")
ax.set_ylabel("Number of Cases")
ax.set_title(f"Trend for {selected_citation}")

st.pyplot(fig)

st.subheader("Sample Cases")

display_cols = [
    "year",
    "title",
    "court",
    "citation"
]

available_cols = [c for c in display_cols if c in citation_df.columns]

st.dataframe(
    citation_df[available_cols].head(25),
    use_container_width=True
)
