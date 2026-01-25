import streamlit as st
import pandas as pd
import cache_utils
import ui_components

st.title("Citation Analytics")

@st.cache_data(ttl=1800)
def load_data(years=None):
    """
    Load data from S3 using cache_utils.
    TTL: 30 minutes - data doesn't change frequently.
    Using st.cache_data because DataFrame is serializable.
    """
    return cache_utils.get_combined_metadata(years)

df = load_data()

if df is None or len(df) == 0:
    st.error("Unable to load data. Please check your connection to AWS S3.")
    st.stop()

if "citation" not in df.columns:
    st.error("Citation column not found in dataset.")
    st.stop()

col1, col2 = st.columns([3, 2])

with col1:
    search_term = ui_components.render_search_bar("citation_search")

with col2:
    selected_years = ui_components.render_year_filter(df, "citations_years")

if selected_years:
    filtered_df = df[df["year"].isin(selected_years)]
else:
    filtered_df = df

if search_term:
    filtered_df = filtered_df[
        filtered_df["citation"].apply(
            lambda lst: any(search_term.lower() in str(c).lower() for c in lst) if isinstance(lst, list) else search_term.lower() in str(lst).lower()
        )
    ]

st.subheader("Citation Summary")

c1, c2, c3 = st.columns(3)

with c1:
    st.metric("Total Cases", len(filtered_df))

with c2:
    try:
        unique_citations = filtered_df.explode("citation")["citation"].nunique()
        st.metric("Unique Citations", unique_citations)
    except:
        st.metric("Unique Citations", "N/A")

with c3:
    year_range = (min(selected_years), max(selected_years)) if selected_years else (int(df['year'].min()), int(df['year'].max()))
    st.metric("Years Covered", f"{year_range[0]} - {year_range[1]}")

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

if len(top_citations) > 0:
    citation_data = pd.DataFrame({
        'citation': top_citations["citation"],
        'case_count': top_citations["case_count"]
    })

    chart = ui_components.create_bar_chart(
        citation_data,
        'citation',
        'case_count',
        'Most Frequent Citations',
        height=400,
        horizontal=True
    )

    st.altair_chart(chart, width='stretch')
else:
    st.info("No citation data available")

st.subheader("Citation Trends Over Time")

if len(top_citations) > 0:
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

    if len(trend) > 0:
        trend_chart = ui_components.create_line_chart(
            trend,
            'year',
            'case_count',
            title=f'Citation Trend: {selected_citation}',
            height=300
        )
        st.altair_chart(trend_chart, width='stretch')
    else:
        st.info("No trend data available for this citation")

    st.subheader("Sample Cases")

    display_cols = ["year", "title", "court", "citation"]
    if "judge" in citation_df.columns:
        display_cols.append("judge")
    if "petitioner" in citation_df.columns:
        display_cols.append("petitioner")
    if "respondent" in citation_df.columns:
        display_cols.append("respondent")
    if "decision_date" in citation_df.columns:
        display_cols.append("decision_date")
    if "disposal_nature" in citation_df.columns:
        display_cols.append("disposal_nature")
    if "case_id" in citation_df.columns:
        display_cols.append("case_id")

    col_config = {}
    for col in display_cols:
        if col == "year":
            col_config[col] = st.column_config.NumberColumn("Year", width="small")
        elif col == "title":
            col_config[col] = st.column_config.TextColumn("Case Title", width="large")
        elif col in ["citation", "judge", "petitioner", "respondent"]:
            col_config[col] = st.column_config.ListColumn(col.title(), width="small")
        else:
            col_config[col] = st.column_config.TextColumn(col.replace("_", " ").title(), width="medium")

    st.dataframe(
        citation_df[display_cols].head(25),
        width='stretch',
        column_config=col_config
    )
else:
    st.info("No citations available to display trends")

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
