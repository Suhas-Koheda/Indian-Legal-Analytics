import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import altair as alt
import re

st.title("Citation Analytics")

@st.cache_data
def load_data():
    return pd.read_parquet("data/base_for_dashboard.parquet")

df = load_data()

if "citation" not in df.columns:
    st.error("Citation column not found in dataset.")
    st.stop()

col1, col2 = st.columns([3, 2])

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

citation_data = pd.DataFrame({
    'citation': top_citations["citation"],
    'case_count': top_citations["case_count"]
})

chart = alt.Chart(citation_data).mark_bar(color='#4CAF50', opacity=0.9).encode(
    y=alt.Y('citation:N', sort='-x', title='Citation'),
    x=alt.X('case_count:Q', title='Number of Cases'),
    tooltip=['citation', 'case_count']
).properties(
    title='Most Frequent Citations',
    height=400
).configure_axis(
    labelFontSize=10,
    titleFontSize=11,
    titleFontWeight='bold'
).configure_title(
    fontSize=14,
    fontWeight='bold'
)

st.altair_chart(chart, use_container_width=True)

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

trend_chart = alt.Chart(trend).mark_line(point=True, color='#9C27B0', size=3).encode(
    x=alt.X('year:O', title='Year'),
    y=alt.Y('case_count:Q', title='Number of Cases'),
    tooltip=['year', 'case_count']
).properties(
    title=f'Citation Trend: {selected_citation}',
    height=300
).configure_axis(
    labelFontSize=10,
    titleFontSize=11,
    titleFontWeight='bold'
).configure_title(
    fontSize=14,
    fontWeight='bold'
)

st.altair_chart(trend_chart, use_container_width=True)

st.subheader("Sample Cases")

st.dataframe(
    citation_df[["year", "title", "court", "citation", "judge", "petitioner", "respondent",
                "decision_date", "disposal_nature", "author_judge", "case_id", "cnr",
                "available_languages", "description"]].head(25),
    use_container_width=True,
    column_config={
        "year": st.column_config.NumberColumn("Year", width="small"),
        "title": st.column_config.TextColumn("Case Title", width="large"),
        "court": st.column_config.TextColumn("Court", width="medium"),
        "citation": st.column_config.ListColumn("Citations", width="small"),
        "judge": st.column_config.ListColumn("Judges", width="small"),
        "petitioner": st.column_config.ListColumn("Petitioners", width="small"),
        "respondent": st.column_config.ListColumn("Respondents", width="small"),
        "decision_date": st.column_config.TextColumn("Decision Date", width="small"),
        "disposal_nature": st.column_config.TextColumn("Disposal Nature", width="small"),
        "author_judge": st.column_config.ListColumn("Author Judge", width="small"),
        "case_id": st.column_config.TextColumn("Case ID", width="small"),
        "cnr": st.column_config.TextColumn("CNR", width="small"),
        "available_languages": st.column_config.ListColumn("Languages", width="small"),
        "description": st.column_config.TextColumn("Description", width="medium")
    }
)

st.markdown("---")
st.markdown("### 📚 Data Attribution")
st.markdown("""
**Indian Supreme Court Judgments Dataset**

This dashboard uses data from the Indian Supreme Court Judgments dataset, which contains:
- Supreme Court judgments from 1950 to present
- Structured metadata and case information
- Licensed under Creative Commons Attribution 4.0 (CC-BY-4.0)

**Source:** [https://github.com/vanga/indian-supreme-court-judgments](https://github.com/vanga/indian-supreme-court-judgments)
""")
