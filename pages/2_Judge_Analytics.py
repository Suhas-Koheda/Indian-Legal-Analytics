import streamlit as st
import pandas as pd
import cache_utils
import ui_components

st.title("Judge Analytics")

@st.cache_data(ttl=1800)
def load_data(years=None):
    """
    Load data from S3 using cache_utils.
    TTL: 30 minutes - data doesn't change frequently.
    Using st.cache_data because DataFrame is serializable.
    """
    return cache_utils.get_combined_metadata(years)

@st.cache_data(ttl=900)
def compute_judge_stats(df, selected_years):
    """Compute judge statistics with caching"""
    if selected_years:
        filtered_df = df[df["year"].isin(selected_years)]
    else:
        filtered_df = df

    if 'judge' not in df.columns:
        return pd.DataFrame(columns=["judge", "first_year", "last_year", "total_cases", "years_active", "avg_cases_per_year"])

    judge_stats = (
        filtered_df
        .explode("judge")
        .dropna(subset=["judge"])
        .groupby("judge")
        .agg({
            "year": ["min", "max", "count", "nunique"]
        })
        .reset_index()
    )

    judge_stats.columns = ["judge", "first_year", "last_year", "total_cases", "years_active"]
    judge_stats["avg_cases_per_year"] = judge_stats["total_cases"] / judge_stats["years_active"]
    judge_stats = judge_stats.sort_values("total_cases", ascending=False)

    return judge_stats

@st.cache_data(ttl=600)
def compute_judge_year_trends(df, selected_years, selected_judge):
    """Compute year-wise trends for a specific judge"""
    if selected_years:
        filtered_df = df[df["year"].isin(selected_years)]
    else:
        filtered_df = df

    if 'judge' not in df.columns:
        return pd.DataFrame(columns=["year", "case_count"])

    judge_cases = filtered_df[
        filtered_df["judge"].apply(lambda x: selected_judge in x if isinstance(x, list) else False)
    ]

    return (
        judge_cases.groupby("year")
        .size()
        .reset_index(name="case_count")
        .sort_values("year")
    )

df = load_data()

if df is None or len(df) == 0:
    st.error("Unable to load data. Please check your connection to AWS S3.")
    st.stop()

col1, col2 = st.columns([3, 2])

with col1:
    search_term = ui_components.render_search_bar("judge_search")

with col2:
    col_a, col_b = st.columns([3, 2])

    with col_a:
        selected_years = ui_components.render_year_filter(df, "judge_years")

    with col_b:
        sort_by = st.selectbox(
            "Sort by",
            ["Name", "Case Count"],
            key="judge_sort"
        )

if selected_years:
    filtered_df = df[df["year"].isin(selected_years)]
else:
    filtered_df = df

if 'judge' not in filtered_df.columns:
    st.error("Judge data not available in the dataset.")
    st.stop()

judge_stats = compute_judge_stats(df, selected_years)

if search_term:
    judge_stats = judge_stats[
        judge_stats["judge"].str.contains(search_term, case=False, na=False)
    ]

if sort_by == "Case Count":
    judge_stats = judge_stats.sort_values("total_cases", ascending=False)
else:
    judge_stats = judge_stats.sort_values("judge")

if len(judge_stats) == 0:
    st.warning("No judges found for the selected criteria.")
    st.stop()

col1, col2 = st.columns([1, 2])

with col1:
    selected_judge = st.selectbox(
        "Select Judge",
        judge_stats["judge"].tolist(),
        key="judge_select"
    )

with col2:
    show_all_cases = st.checkbox("Show all cases", value=False, key="judge_show_all")

judge_data = judge_stats[judge_stats["judge"] == selected_judge].iloc[0]

judge_df = filtered_df[
    filtered_df["judge"].apply(lambda lst: selected_judge in lst if isinstance(lst, list) else False)
]

st.subheader(f"⚖️ Justice {selected_judge}")

cols = st.columns(3, gap="small")

with cols[0].container(border=True):
    st.metric("📄 Total Cases", f"{int(judge_data['total_cases'])}")

with cols[1].container(border=True):
    st.metric("📅 Years Active", f"{int(judge_data['years_active'])}")

with cols[2].container(border=True):
    st.metric("📈 Avg Cases/Year", round(judge_data['avg_cases_per_year'], 1))

st.subheader("📈 Year-wise Case Load")

cases_per_year = compute_judge_year_trends(df, selected_years, selected_judge)

if len(cases_per_year) > 0:
    chart = ui_components.create_line_chart(
        cases_per_year,
        'year',
        'case_count',
        title=f'Cases handled by {selected_judge}',
        height=300
    )
    st.altair_chart(chart, width='stretch')
else:
    st.info("No case data available for this judge in the selected years")

st.subheader("Cases Handled by This Judge")

display_count = len(judge_df) if show_all_cases else 25

display_cols = ["year", "title", "court"]
if "citation" in judge_df.columns:
    display_cols.append("citation")
if "petitioner" in judge_df.columns:
    display_cols.append("petitioner")
if "respondent" in judge_df.columns:
    display_cols.append("respondent")
if "decision_date" in judge_df.columns:
    display_cols.append("decision_date")
if "disposal_nature" in judge_df.columns:
    display_cols.append("disposal_nature")
if "case_id" in judge_df.columns:
    display_cols.append("case_id")

col_config = {}
for col in display_cols:
    if col == "year":
        col_config[col] = st.column_config.NumberColumn("Year", width="small")
    elif col == "title":
        col_config[col] = st.column_config.TextColumn("Case Title", width="large")
    elif col in ["citation", "petitioner", "respondent"]:
        col_config[col] = st.column_config.ListColumn(col.title(), width="small")
    else:
        col_config[col] = st.column_config.TextColumn(col.replace("_", " ").title(), width="medium")

st.dataframe(
    judge_df[display_cols].head(display_count),
    width='stretch',
    column_config=col_config
)

if not show_all_cases and len(judge_df) > 25:
    st.info(f"Showing first 25 of {len(judge_df)} cases. Check 'Show all cases' to see everything.")

st.subheader("Judge Comparison Table")

judge_comparison = judge_stats.head(25).copy()

if 'court' in filtered_df.columns:
    judge_comparison["courts_judged"] = judge_comparison["judge"].apply(
        lambda j: len(filtered_df[filtered_df["judge"].apply(lambda x: j in x if isinstance(x, list) else False)]["court"].unique())
    )
else:
    judge_comparison["courts_judged"] = 0

display_comparison_cols = ["judge", "total_cases", "years_active", "avg_cases_per_year", "first_year", "last_year"]
if "courts_judged" in judge_comparison.columns:
    display_comparison_cols.append("courts_judged")

comparison_col_config = {}
for col in display_comparison_cols:
    if col == "judge":
        comparison_col_config[col] = st.column_config.TextColumn("Judge Name", width="medium")
    elif col == "avg_cases_per_year":
        comparison_col_config[col] = st.column_config.NumberColumn("Avg/Year", width="small", format="%.1f")
    else:
        comparison_col_config[col] = st.column_config.NumberColumn(col.replace("_", " ").title(), width="small")

st.dataframe(
    judge_comparison[display_comparison_cols],
    width='stretch',
    column_config=comparison_col_config
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
