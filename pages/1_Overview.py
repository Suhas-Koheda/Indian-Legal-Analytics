import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import altair as alt

st.title("Dashboard Overview")

@st.cache_data(ttl=1800)  # Cache for 30 minutes
def load_data():
    return pd.read_parquet("data/base_for_dashboard.parquet")

@st.cache_data(ttl=900)  # Cache for 15 minutes
def compute_overview_stats(df, selected_years):
    """Compute overview statistics with caching"""
    if selected_years:
        filtered_df = df[df["year"].isin(selected_years)]
    else:
        filtered_df = df

    return {
        "total_cases": len(filtered_df),
        "year_range": f"{min(selected_years) if selected_years else int(df['year'].min())}-{max(selected_years) if selected_years else int(df['year'].max())}",
        "unique_judges": filtered_df.explode("judge")["judge"].nunique(),
        "unique_citations": filtered_df.explode("citation")["citation"].nunique(),
        "avg_cases_per_year": len(filtered_df) / max(1, len(selected_years) if selected_years else (int(df['year'].max()) - int(df['year'].min()) + 1))
    }

@st.cache_data(ttl=600)  # Cache for 10 minutes
def compute_case_trends(df, selected_years):
    """Compute case volume trends with caching"""
    if selected_years:
        filtered_df = df[df["year"].isin(selected_years)]
    else:
        filtered_df = df

    return (
        filtered_df.groupby("year")
        .size()
        .reset_index(name="case_count")
        .sort_values("year")
    )

@st.cache_data(ttl=600)  # Cache for 10 minutes
def compute_top_judges_with_years(df, selected_years):
    """Compute top judges with career year information"""
    if selected_years:
        filtered_df = df[df["year"].isin(selected_years)]
    else:
        filtered_df = df

    judge_stats = (
        filtered_df
        .explode("judge")
        .dropna(subset=["judge"])
        .groupby("judge")
        .agg({
            "year": ["min", "max", "count"]
        })
        .reset_index()
    )

    judge_stats.columns = ["judge", "first_year", "last_year", "case_count"]
    judge_stats["year_range"] = judge_stats["first_year"].astype(str) + "-" + judge_stats["last_year"].astype(str)
    judge_stats = judge_stats.sort_values("case_count", ascending=False).head(10)

    return judge_stats

df = load_data()

col1, col2 = st.columns([3, 2])

with col1:
    search_term = st.text_input("Search cases", "", key="overview_search")

with col2:
    min_year = int(df["year"].min())
    max_year = int(df["year"].max())
    years = list(range(min_year, max_year + 1))
    selected_years = st.multiselect(
        "Select Years",
        years,
        default=[min_year, max_year],
        key="overview_years"
    )

    if selected_years:
        year_range = (min(selected_years), max(selected_years))
    else:
        year_range = (min_year, max_year)

if selected_years:
    filtered_df = df[df["year"].isin(selected_years)]
else:
    filtered_df = df

if search_term:
    filtered_df = filtered_df[
        filtered_df["title"].str.contains(search_term, case=False, na=False)
    ]

st.subheader("📊 Dataset Summary")

cols = st.columns(5, gap="small")

with cols[0].container(border=True):
    st.metric("📄 Total Cases", f"{len(filtered_df):,}")

with cols[1].container(border=True):
    st.metric("📅 Years Covered", f"{year_range[0]}-{year_range[1]}")

with cols[2].container(border=True):
    st.metric("⚖️ Judges", f"{filtered_df.explode('judge')['judge'].nunique():,}")

with cols[3].container(border=True):
    st.metric("📜 Citations", f"{filtered_df.explode('citation')['citation'].nunique():,}")

with cols[4].container(border=True):
    avg_cases = len(filtered_df) / max(1, year_range[1] - year_range[0] + 1)
    st.metric("📈 Avg Cases/Year", round(avg_cases, 1))

st.subheader("📈 Case Volume Trends")

cases_per_year = compute_case_trends(df, selected_years)

chart = alt.Chart(cases_per_year).mark_bar(color='#FF6B35', opacity=0.8).encode(
    x=alt.X('year:O', title='Year'),
    y=alt.Y('case_count:Q', title='Number of Cases'),
    tooltip=['year', 'case_count']
).properties(
    title='Annual Case Volume Trends',
    height=300
).configure_axis(
    labelFontSize=11,
    titleFontSize=12,
    titleFontWeight='bold'
).configure_title(
    fontSize=14,
    fontWeight='bold'
)

st.altair_chart(chart, use_container_width=True)

cols = st.columns(2, gap="medium")

with cols[0].container(border=True, height=400):
    st.subheader("👨‍⚖️ Top Judges by Case Volume")

    judge_stats = compute_top_judges_with_years(df, selected_years)
    judge_data = pd.DataFrame({
        'judge': judge_stats["judge"],
        'case_count': judge_stats["case_count"],
        'year_range': judge_stats["year_range"]
    })

    judge_chart = alt.Chart(judge_data.head(10)).mark_bar(color='#FF6B35', opacity=0.9).encode(
        y=alt.Y('judge:N', sort='-x', title='Judge'),
        x=alt.X('case_count:Q', title='Number of Cases'),
        tooltip=['judge', 'case_count', 'year_range']
    ).properties(
        title='Most Active Judges (with Career Years)',
        height=300
    ).configure_axis(
        labelFontSize=10,
        titleFontSize=11,
        titleFontWeight='bold'
    ).configure_title(
        fontSize=12,
        fontWeight='bold'
    )

    st.altair_chart(judge_chart, use_container_width=True)

with cols[1].container(border=True, height=400):
    st.subheader("📜 Most Cited Legal References")

    filtered_df = df[df["year"].isin(selected_years)] if selected_years else df

    top_citations = (
        filtered_df.explode("citation")
        .dropna(subset=["citation"])
        .groupby("citation")
        .size()
        .reset_index(name="case_count")
        .sort_values("case_count", ascending=False)
        .head(10)
    )
    citation_data = pd.DataFrame({
        'citation': top_citations["citation"],
        'case_count': top_citations["case_count"]
    })

    citation_chart = alt.Chart(citation_data).mark_bar(color='#4CAF50', opacity=0.9).encode(
        y=alt.Y('citation:N', sort='-x', title='Citation'),
        x=alt.X('case_count:Q', title='Number of Cases'),
        tooltip=['citation', 'case_count']
    ).properties(
        title='Most Cited Legal References',
        height=300
    ).configure_axis(
        labelFontSize=10,
        titleFontSize=11,
        titleFontWeight='bold'
    ).configure_title(
        fontSize=12,
        fontWeight='bold'
    )

    st.altair_chart(citation_chart, use_container_width=True)

st.subheader("Recent Cases")

recent_cases = filtered_df[
    ["year", "title", "court", "judge", "citation", "petitioner", "respondent",
     "decision_date", "disposal_nature", "author_judge", "case_id", "cnr"]
].sort_values("year", ascending=False).head(15)

st.dataframe(
    recent_cases,
    use_container_width=True,
    column_config={
        "year": st.column_config.NumberColumn("Year", width="small"),
        "title": st.column_config.TextColumn("Case Title", width="large"),
        "court": st.column_config.TextColumn("Court", width="medium"),
        "judge": st.column_config.ListColumn("Judges", width="small"),
        "citation": st.column_config.ListColumn("Citations", width="small"),
        "petitioner": st.column_config.ListColumn("Petitioners", width="small"),
        "respondent": st.column_config.ListColumn("Respondents", width="small"),
        "decision_date": st.column_config.TextColumn("Decision Date", width="medium"),
        "disposal_nature": st.column_config.TextColumn("Disposal Nature", width="medium"),
        "author_judge": st.column_config.ListColumn("Author Judge", width="small"),
        "case_id": st.column_config.TextColumn("Case ID", width="small"),
        "cnr": st.column_config.TextColumn("CNR", width="small")
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
