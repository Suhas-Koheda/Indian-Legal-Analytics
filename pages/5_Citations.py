import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import re

st.title("Citation Analytics")

@st.cache_data
def load_data():
    return pd.read_parquet("data/base_for_dashboard.parquet")

df = load_data()

if "citation" not in df.columns:
    st.error("Citation column not found in dataset.")
    st.stop()

col1, col2, col3 = st.columns([2, 1, 1])

with col1:
    search_term = st.text_input("Search citations", "", key="citation_search")

with col2:
    min_year = int(df["year"].min())
    max_year = int(df["year"].max())
    years = list(range(min_year, max_year + 1))
    selected_years = st.multiselect(
        "Select Years",
        years,
        default=[min_year, max_year],
        key="citations_years"
    )

with col3:
    if selected_years:
        year_range = (min(selected_years), max(selected_years))
    else:
        year_range = (min_year, max_year)

if selected_years:
    filtered_df = df[df["year"].isin(selected_years)]
else:
    filtered_df = df

st.subheader("Citation Summary")

c1, c2, c3 = st.columns(3)

with c1:
    st.metric("Total Cases", len(filtered_df))

with c2:
    st.metric(
        "Unique Citations",
        filtered_df.explode("citation")["citation"].nunique()
    )

with c3:
    st.metric(
        "Years Covered",
        f"{year_range[0]} - {year_range[1]}"
    )

st.subheader("Most Frequent Citations")

top_citations = (
    filtered_df
    .explode("citation")
    .dropna(subset=["citation"])
    .groupby("citation")
    .size()
    .reset_index(name="case_count")
    .sort_values("case_count", ascending=False)
    .head(20)
)

fig, ax = plt.subplots(figsize=(6, 6))
ax.barh(top_citations["citation"], top_citations["case_count"], alpha=0.8, color='lightgreen', edgecolor='darkgreen', linewidth=0.5)
ax.invert_yaxis()
ax.set_xlabel("Number of Cases", fontsize=10)
ax.set_ylabel("Citation", fontsize=10)
ax.set_title("Most Frequent Citations", fontsize=12, fontweight='bold')
ax.grid(axis='x', alpha=0.3)
ax.tick_params(axis='both', which='major', labelsize=9)

st.pyplot(fig)

st.subheader("Citation Trends Over Time")

selected_citation = st.selectbox(
    "Select a Citation",
    top_citations["citation"].tolist()
)

citation_df = filtered_df[
    filtered_df["citation"].apply(
        lambda lst: selected_citation in lst if isinstance(lst, list) else False
    )
]

trend = (
    citation_df.groupby("year")
    .size()
    .reset_index(name="case_count")
)

fig, ax = plt.subplots(figsize=(8, 4))
ax.plot(trend["year"], trend["case_count"], marker='o', color='purple', linewidth=2, markersize=5)
ax.fill_between(trend["year"], trend["case_count"], alpha=0.3, color='purple')
ax.set_xlabel("Year", fontsize=10)
ax.set_ylabel("Number of Cases", fontsize=10)
ax.set_title(f"Citation Trend: {selected_citation}", fontsize=12, fontweight='bold')
ax.grid(True, alpha=0.3)
ax.tick_params(axis='both', which='major', labelsize=9)

st.pyplot(fig)

st.subheader("Sample Cases")

st.dataframe(
    citation_df[["year", "title", "court", "citation", "judge", "petitioner", "respondent", "decision_date"]].head(25),
    use_container_width=True,
    column_config={
        "year": st.column_config.NumberColumn("Year", width="small"),
        "title": st.column_config.TextColumn("Case Title", width="large"),
        "court": st.column_config.TextColumn("Court", width="medium"),
        "citation": st.column_config.ListColumn("Citations", width="medium"),
        "judge": st.column_config.ListColumn("Judges", width="small"),
        "petitioner": st.column_config.ListColumn("Petitioners", width="medium"),
        "respondent": st.column_config.ListColumn("Respondents", width="medium"),
        "decision_date": st.column_config.TextColumn("Decision Date", width="medium")
    }
)
