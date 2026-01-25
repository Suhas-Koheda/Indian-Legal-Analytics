import streamlit as st
import pandas as pd
import cache_utils
import search
import ui_components

st.title("Dashboard Overview")

@st.cache_data(ttl=1800)
def load_data(years=None):
    """
    Load data from S3 using cache_utils.
    TTL: 30 minutes - data doesn't change frequently.
    Using st.cache_data because DataFrame is serializable.
    """
    return cache_utils.get_combined_metadata(years)

@st.cache_data(ttl=900)
def compute_overview_stats(df, selected_years):
    """Compute overview statistics with caching"""
    if selected_years:
        filtered_df = df[df["year"].isin(selected_years)]
    else:
        filtered_df = df

    judge_col = 'judge' if 'judge' in df.columns else None
    citation_col = 'citation' if 'citation' in df.columns else None
    
    unique_judges = 0
    unique_citations = 0
    
    if judge_col:
        try:
            unique_judges = filtered_df.explode("judge")["judge"].nunique()
        except:
            pass
    
    if citation_col:
        try:
            unique_citations = filtered_df.explode("citation")["citation"].nunique()
        except:
            pass

    year_span = len(selected_years) if selected_years else (int(df['year'].max()) - int(df['year'].min()) + 1)
    
    return {
        "total_cases": len(filtered_df),
        "year_range": f"{min(selected_years) if selected_years else int(df['year'].min())}-{max(selected_years) if selected_years else int(df['year'].max())}",
        "unique_judges": unique_judges,
        "unique_citations": unique_citations,
        "avg_cases_per_year": len(filtered_df) / max(1, year_span)
    }

@st.cache_data(ttl=600)
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

@st.cache_data(ttl=600)
def compute_top_judges_with_years(df, selected_years):
    """Compute top judges with career year information"""
    if selected_years:
        filtered_df = df[df["year"].isin(selected_years)]
    else:
        filtered_df = df

    if 'judge' not in df.columns:
        return pd.DataFrame(columns=["judge", "first_year", "last_year", "case_count", "year_range"])

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

if df is None or len(df) == 0:
    st.error("Unable to load data. Please check your connection to AWS S3.")
    st.stop()

col1, col2 = st.columns([3, 2])

with col1:
    search_term = ui_components.render_search_bar("overview_search")

with col2:
    selected_years = ui_components.render_year_filter(df, "overview_years")

if selected_years:
    filtered_df = df[df["year"].isin(selected_years)]
else:
    filtered_df = df

if search_term:
    filtered_df = search.search_cases(filtered_df, search_term)

st.subheader("📊 Dataset Summary")

cols = st.columns(5, gap="small")

stats = compute_overview_stats(df, selected_years)

with cols[0].container(border=True):
    st.metric("📄 Total Cases", f"{stats['total_cases']:,}")

with cols[1].container(border=True):
    st.metric("📅 Years Covered", stats['year_range'])

with cols[2].container(border=True):
    st.metric("⚖️ Judges", f"{stats['unique_judges']:,}")

with cols[3].container(border=True):
    st.metric("📜 Citations", f"{stats['unique_citations']:,}")

with cols[4].container(border=True):
    st.metric("📈 Avg Cases/Year", round(stats['avg_cases_per_year'], 1))

st.subheader("📈 Case Volume Trends")

cases_per_year = compute_case_trends(df, selected_years)

chart = ui_components.create_case_volume_chart(
    df[df["year"].isin(selected_years)] if selected_years else df,
    title="Annual Case Volume Trends",
    height=300
)

st.altair_chart(chart, width='stretch')

cols = st.columns(2, gap="medium")

with cols[0].container(border=True, height=400):
    st.subheader("👨‍⚖️ Top Judges by Case Volume")

    judge_stats = compute_top_judges_with_years(df, selected_years)
    
    if len(judge_stats) > 0:
        judge_data = pd.DataFrame({
            'judge': judge_stats["judge"],
            'case_count': judge_stats["case_count"],
            'year_range': judge_stats["year_range"]
        })

        judge_chart = ui_components.create_bar_chart(
            judge_data.head(10),
            'judge',
            'case_count',
            'Most Active Judges (with Career Years)',
            height=300,
            horizontal=True
        )

        st.altair_chart(judge_chart, use_container_width=True)
    else:
        st.info("No judge data available")

with cols[1].container(border=True, height=400):
    st.subheader("📜 Most Cited Legal References")

    filtered_for_citations = df[df["year"].isin(selected_years)] if selected_years else df

    if 'citation' in filtered_for_citations.columns:
        top_citations = (
            filtered_for_citations.explode("citation")
            .dropna(subset=["citation"])
            .groupby("citation")
            .size()
            .reset_index(name="case_count")
            .sort_values("case_count", ascending=False)
            .head(10)
        )
        
        if len(top_citations) > 0:
            citation_data = pd.DataFrame({
                'citation': top_citations["citation"],
                'case_count': top_citations["case_count"]
            })

            citation_chart = ui_components.create_bar_chart(
                citation_data,
                'citation',
                'case_count',
                'Most Cited Legal References',
                height=300,
                horizontal=True
            )

            st.altair_chart(citation_chart, use_container_width=True)
        else:
            st.info("No citation data available")
    else:
        st.info("Citation data not available")

st.subheader("Recent Cases")

display_cols = ["year", "title", "court"]
if "judge" in filtered_df.columns:
    display_cols.append("judge")
if "citation" in filtered_df.columns:
    display_cols.append("citation")
if "petitioner" in filtered_df.columns:
    display_cols.append("petitioner")
if "respondent" in filtered_df.columns:
    display_cols.append("respondent")
if "decision_date" in filtered_df.columns:
    display_cols.append("decision_date")
if "disposal_nature" in filtered_df.columns:
    display_cols.append("disposal_nature")
if "author_judge" in filtered_df.columns:
    display_cols.append("author_judge")
if "case_id" in filtered_df.columns:
    display_cols.append("case_id")
if "cnr" in filtered_df.columns:
    display_cols.append("cnr")

recent_cases = filtered_df[display_cols].sort_values("year", ascending=False).head(15)

col_config = {}
for col in display_cols:
    if col == "year":
        col_config[col] = st.column_config.NumberColumn("Year", width="small")
    elif col == "title":
        col_config[col] = st.column_config.TextColumn("Case Title", width="large")
    elif col in ["judge", "citation", "petitioner", "respondent", "author_judge"]:
        col_config[col] = st.column_config.ListColumn(col.title(), width="small")
    else:
        col_config[col] = st.column_config.TextColumn(col.replace("_", " ").title(), width="medium")

st.dataframe(recent_cases, width='stretch', column_config=col_config)

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
