import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

st.title("Dashboard Overview")

@st.cache_data
def load_data():
    return pd.read_parquet("data/base_for_dashboard.parquet")

df = load_data()

col1, col2, col3 = st.columns([2, 1, 1])

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

with col3:
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

st.subheader("Dataset Summary")

c1, c2, c3, c4, c5 = st.columns(5)

with c1:
    st.metric("Total Cases", len(filtered_df))

with c2:
    st.metric("Years Covered", f"{year_range[0]}-{year_range[1]}")

with c3:
    st.metric("Judges", filtered_df.explode("judge")["judge"].nunique())

with c4:
    st.metric("Citations", filtered_df.explode("citation")["citation"].nunique())

with c5:
    avg_cases = len(filtered_df) / max(1, year_range[1] - year_range[0] + 1)
    st.metric("Avg Cases/Year", round(avg_cases, 1))

st.subheader("Case Volume Trends")

cases_per_year = (
    filtered_df.groupby("year")
    .size()
    .reset_index(name="case_count")
    .sort_values("year")
)

fig, ax = plt.subplots(figsize=(8, 4))
bars = ax.bar(cases_per_year["year"], cases_per_year["case_count"], alpha=0.7, color='skyblue')
ax.plot(cases_per_year["year"], cases_per_year["case_count"], marker='o', color='red', linewidth=2)

ax.set_xlabel("Year")
ax.set_ylabel("Number of Cases")
ax.set_title("Annual Case Volume")
ax.grid(True, alpha=0.3)

st.pyplot(fig)

col1, col2 = st.columns(2)

with col1:
    st.subheader("Top Judges by Case Volume")

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

    judge_labels = [f"{judge}\n({years})" for judge, years in zip(judge_stats["judge"], judge_stats["year_range"])]

    fig, ax = plt.subplots(figsize=(6, 5))
    bars = ax.barh(judge_labels, judge_stats["case_count"], color='lightcoral', alpha=0.8)
    ax.invert_yaxis()
    ax.set_xlabel("Number of Cases")
    ax.set_title("Most Active Judges (with Career Years)", fontsize=12, fontweight='bold')
    ax.grid(axis='x', alpha=0.3)

    for bar, count in zip(bars, judge_stats["case_count"]):
        ax.text(count + 0.5, bar.get_y() + bar.get_height()/2, str(count),
                ha='left', va='center', fontsize=9, fontweight='bold')

    st.pyplot(fig)

with col2:
    st.subheader("Most Cited Legal References")

    top_citations = (
        filtered_df
        .explode("citation")
        .dropna(subset=["citation"])
        .groupby("citation")
        .size()
        .reset_index(name="case_count")
        .sort_values("case_count", ascending=False)
        .head(10)
    )

    fig, ax = plt.subplots(figsize=(5, 4))
    bars = ax.barh(top_citations["citation"], top_citations["case_count"], color='lightgreen')
    ax.invert_yaxis()
    ax.set_xlabel("Number of Cases")
    ax.set_title("Most Cited Legal References")

    st.pyplot(fig)

st.subheader("Recent Cases")

st.dataframe(
    filtered_df[["year", "title", "court", "judge", "citation"]]
    .sort_values("year", ascending=False)
    .head(20),
    use_container_width=True,
    column_config={
        "year": st.column_config.NumberColumn("Year", width="small"),
        "title": st.column_config.TextColumn("Case Title", width="large"),
        "court": st.column_config.TextColumn("Court", width="medium"),
        "judge": st.column_config.ListColumn("Judges", width="medium"),
        "citation": st.column_config.ListColumn("Citations", width="medium")
    }
)
