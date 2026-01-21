import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(
    page_title="Overview | Legal Analytics",
    layout="wide"
)

st.title("📊 Legal Analytics Dashboard – Overview")

@st.cache_data
def load_data():
    base = pd.read_parquet("data/base_for_dashboard.parquet")
    cases_per_judge = pd.read_parquet("data/total_cases_per_judge.parquet")
    cases_per_article = pd.read_parquet("data/total_cases_per_article.parquet")
    return base, cases_per_judge, cases_per_article

base_df, judge_df, article_df = load_data()
st.subheader("📌 Dataset Summary")
col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Total Cases", len(base_df))

with col2:
    st.metric("Total Judges", base_df["judge_list"].explode().nunique())

with col3:
    st.metric("Years Covered", f"{base_df['year'].min()} – {base_df['year'].max()}")
st.subheader("📈 Cases per Year")

cases_per_year = (
    base_df.groupby("year")
    .size()
    .reset_index(name="case_count")
    .sort_values("year")
)

fig, ax = plt.subplots()
ax.plot(cases_per_year["year"], cases_per_year["case_count"])
ax.set_xlabel("Year")
ax.set_ylabel("Number of Cases")

st.pyplot(fig)

st.subheader("👨‍⚖️ Top Judges by Case Volume")

top_judges = judge_df.head(15)

fig, ax = plt.subplots()
ax.barh(top_judges["judge_list"], top_judges["total_cases"])
ax.invert_yaxis()
ax.set_xlabel("Number of Cases")
ax.set_ylabel("Judge")

st.pyplot(fig)
st.subheader("📜 Most Litigated Constitutional Articles")

top_articles = article_df.head(15)

fig, ax = plt.subplots()
ax.barh(top_articles["article_list"], top_articles["total_cases"])
ax.invert_yaxis()
ax.set_xlabel("Number of Cases")
ax.set_ylabel("Article")

st.pyplot(fig)
st.subheader("🔎 Sample Cases")

display_cols = ["year", "judge_list", "article_list"]
available_cols = [c for c in display_cols if c in base_df.columns]

st.dataframe(
    base_df[available_cols].head(20),
    use_container_width=True
)