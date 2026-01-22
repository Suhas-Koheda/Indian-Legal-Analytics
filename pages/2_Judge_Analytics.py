import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

st.title("Judge Analytics")

@st.cache_data
def load_data():
    return pd.read_parquet("data/base_for_dashboard.parquet")

df = load_data()

col1, col2 = st.columns([3, 2])

with col1:
    search_term = st.text_input("Search judges", "", key="judge_search")

with col2:
    col_a, col_b = st.columns([3, 2])

    with col_a:
        min_year = int(df["year"].min())
        max_year = int(df["year"].max())
        years = list(range(min_year, max_year + 1))
        selected_years = st.multiselect(
            "Select Years",
            years,
            default=[min_year, max_year],
            key="judge_years"
        )

        if selected_years:
            year_range = (min(selected_years), max(selected_years))
        else:
            year_range = (min_year, max_year)

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

judge_stats = (
    filtered_df
    .explode("judge")
    .dropna(subset=["judge"])
    .groupby("judge")
    .agg({
        "year": ["count", "nunique", "min", "max"]
    })
    .reset_index()
)

judge_stats.columns = ["judge", "total_cases", "years_active", "first_year", "last_year"]
judge_stats["avg_cases_per_year"] = judge_stats["total_cases"] / judge_stats["years_active"]

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
    filtered_df["judge"].apply(lambda lst: selected_judge in lst)
]

st.subheader(f"Justice {selected_judge}")

c1, c2, c3, c4 = st.columns(4)

with c1:
    st.metric("Total Cases", int(judge_data["total_cases"]))

with c2:
    st.metric("Years Active", int(judge_data["years_active"]))

with c3:
    st.metric("Avg Cases/Year", round(judge_data["avg_cases_per_year"], 1))

with c4:
    st.metric("Career Span", f"{int(judge_data['first_year'])}-{int(judge_data['last_year'])}")

st.subheader("Year-wise Case Load")

cases_per_year = (
    judge_df.groupby("year")
    .size()
    .reset_index(name="case_count")
    .sort_values("year")
)

fig, ax = plt.subplots(figsize=(8, 4))
ax.bar(cases_per_year["year"], cases_per_year["case_count"], alpha=0.8, color='skyblue', edgecolor='navy', linewidth=0.5)
ax.plot(cases_per_year["year"], cases_per_year["case_count"], marker='o', color='red', linewidth=2, markersize=4)
ax.set_xlabel("Year", fontsize=10)
ax.set_ylabel("Number of Cases", fontsize=10)
ax.set_title(f"Cases handled by {selected_judge}", fontsize=12, fontweight='bold')
ax.grid(True, alpha=0.3)
ax.tick_params(axis='both', which='major', labelsize=9)

st.pyplot(fig)

st.subheader("Cases Handled by This Judge")

display_count = len(judge_df) if show_all_cases else 25

st.dataframe(
    judge_df[["year", "title", "court", "citation", "petitioner", "respondent",
              "decision_date", "disposal_nature", "author_judge", "case_id", "cnr",
              "available_languages"]].head(display_count),
    use_container_width=True,
    column_config={
        "year": st.column_config.NumberColumn("Year", width="small"),
        "title": st.column_config.TextColumn("Case Title", width="large"),
        "court": st.column_config.TextColumn("Court", width="medium"),
        "citation": st.column_config.ListColumn("Citations", width="small"),
        "petitioner": st.column_config.ListColumn("Petitioners", width="small"),
        "respondent": st.column_config.ListColumn("Respondents", width="small"),
        "decision_date": st.column_config.TextColumn("Decision Date", width="small"),
        "disposal_nature": st.column_config.TextColumn("Disposal Nature", width="small"),
        "author_judge": st.column_config.ListColumn("Author Judge", width="small"),
        "case_id": st.column_config.TextColumn("Case ID", width="small"),
        "cnr": st.column_config.TextColumn("CNR", width="small"),
        "available_languages": st.column_config.ListColumn("Languages", width="small")
    }
)

if not show_all_cases and len(judge_df) > 25:
    st.info(f"Showing first 25 of {len(judge_df)} cases. Check 'Show all cases' to see everything.")

st.subheader("Judge Comparison Table")

judge_comparison = judge_stats.head(25).copy()
judge_comparison["courts_judged"] = judge_comparison["judge"].apply(
    lambda j: len(df[df["judge"].apply(lambda x: j in x if isinstance(x, list) else False)]["court"].unique())
)

st.dataframe(
    judge_comparison[["judge", "total_cases", "years_active", "avg_cases_per_year",
                     "first_year", "last_year", "courts_judged"]],
    use_container_width=True,
    column_config={
        "judge": st.column_config.TextColumn("Judge Name", width="medium"),
        "total_cases": st.column_config.NumberColumn("Total Cases", width="small"),
        "years_active": st.column_config.NumberColumn("Years Active", width="small"),
        "avg_cases_per_year": st.column_config.NumberColumn("Avg/Year", width="small", format="%.1f"),
        "first_year": st.column_config.NumberColumn("First Year", width="small"),
        "last_year": st.column_config.NumberColumn("Last Year", width="small"),
        "courts_judged": st.column_config.NumberColumn("Courts Served", width="small")
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
