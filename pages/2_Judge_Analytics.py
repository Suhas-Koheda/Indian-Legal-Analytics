import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

st.title("Judge Analytics")

@st.cache_data
def load_data():
    return pd.read_parquet("data/base_for_dashboard.parquet")

df = load_data()

col1, col2, col3, col4 = st.columns([2, 1, 1, 1])

with col1:
    search_term = st.text_input("Search judges", "", key="judge_search")

with col2:
    min_year = int(df["year"].min())
    max_year = int(df["year"].max())
    years = list(range(min_year, max_year + 1))
    selected_years = st.multiselect(
        "Select Years",
        years,
        default=[min_year, max_year],
        key="judge_years"
    )

with col3:
    if selected_years:
        year_range = (min(selected_years), max(selected_years))
    else:
        year_range = (min_year, max_year)

with col4:
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
    judge_df[["year", "title", "court", "citation"]].head(display_count),
    use_container_width=True,
    column_config={
        "year": st.column_config.NumberColumn("Year", width="small"),
        "title": st.column_config.TextColumn("Case Title", width="large"),
        "court": st.column_config.TextColumn("Court", width="medium"),
        "citation": st.column_config.ListColumn("Citations", width="medium")
    }
)

if not show_all_cases and len(judge_df) > 25:
    st.info(f"Showing first 25 of {len(judge_df)} cases. Check 'Show all cases' to see everything.")

st.subheader("Judge Comparison Table")

st.dataframe(
    judge_stats.head(20),
    use_container_width=True,
    column_config={
        "judge": st.column_config.TextColumn("Judge Name", width="medium"),
        "total_cases": st.column_config.NumberColumn("Total Cases", width="small"),
        "years_active": st.column_config.NumberColumn("Years Active", width="small"),
        "avg_cases_per_year": st.column_config.NumberColumn("Avg/Year", width="small", format="%.1f"),
        "first_year": st.column_config.NumberColumn("First Year", width="small"),
        "last_year": st.column_config.NumberColumn("Last Year", width="small")
    }
)
