import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(
    page_title="Article Analytics | Legal Analytics Dashboard",
    layout="wide"
)

st.title("Article Analytics")

@st.cache_data
def load_data():
    return pd.read_parquet("data/base_for_dashboard.parquet")

df = load_data()

col1, col2 = st.columns([2, 1])

with col1:
    search_term = st.text_input("Search citations", "", key="citation_search")

with col2:
    min_year = int(df["year"].min())
    max_year = int(df["year"].max())
    year_range = st.slider(
        "Year Range",
        min_year,
        max_year,
        (min_year, max_year),
        key="citation_year_range"
    )

filtered_df = df[
    (df["year"] >= year_range[0]) &
    (df["year"] <= year_range[1])
]

if search_term:
    filtered_df = filtered_df[
        filtered_df["citation"].apply(
            lambda lst: any(search_term.lower() in str(c).lower() for c in lst) if isinstance(lst, list) else False
        )
    ]

all_citations = (
    filtered_df
    .explode("citation")["citation"]
    .dropna()
    .sort_values()
    .unique()
)

if len(all_citations) == 0:
    st.warning("No citations found for the selected criteria.")
    st.stop()

col1, col2 = st.columns([1, 2])

with col1:
    selected_citation = st.selectbox(
        "Select Citation",
        all_citations,
        key="citation_select"
    )

with col2:
    show_all_cases = st.checkbox("Show all cases", value=False, key="citation_show_all")

citation_df = filtered_df[
    filtered_df["citation"].apply(lambda lst: selected_citation in lst)
]

st.subheader(f"Citation: {selected_citation}")

c1, c2, c3, c4 = st.columns(4)

with c1:
    st.metric("Total Cases", len(citation_df))

with c2:
    st.metric("Years Referenced", citation_df["year"].nunique())

with c3:
    avg = len(citation_df) / max(citation_df["year"].nunique(), 1)
    st.metric("Avg Cases / Year", round(avg, 2))

with c4:
    judges_count = citation_df.explode("judge")["judge"].nunique()
    st.metric("Unique Judges", judges_count)

st.subheader("Year-wise Citation Frequency")

cases_per_year = (
    citation_df.groupby("year")
    .size()
    .reset_index(name="case_count")
    .sort_values("year")
)

fig, ax = plt.subplots(figsize=(10, 4))
ax.plot(cases_per_year["year"], cases_per_year["case_count"], marker='o')
ax.set_xlabel("Year")
ax.set_ylabel("Number of Cases")
ax.set_title(f"Cases citing {selected_citation}")
ax.grid(True, alpha=0.3)

st.pyplot(fig)

st.subheader("Cases Citing This Citation")

display_count = len(citation_df) if show_all_cases else 25

st.dataframe(
    citation_df[["year", "title", "court", "judge"]].head(display_count),
    use_container_width=True,
    column_config={
        "year": st.column_config.NumberColumn("Year", width="small"),
        "title": st.column_config.TextColumn("Case Title", width="large"),
        "court": st.column_config.TextColumn("Court", width="medium"),
        "judge": st.column_config.ListColumn("Judges", width="medium")
    }
)

if not show_all_cases and len(citation_df) > 25:
    st.info(f"Showing first 25 of {len(citation_df)} cases. Check 'Show all cases' to see everything.")