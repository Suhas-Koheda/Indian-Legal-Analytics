import streamlit as st
import pandas as pd

st.title("Case Explorer")

@st.cache_data
def load_data():
    return pd.read_parquet("data/base_for_dashboard.parquet")

df = load_data()

col1, col2 = st.columns([3, 2])

with col1:
    search_term = st.text_input("Search in case titles", "", key="case_search")

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
            key="case_years"
        )

        if selected_years:
            year_range = (min(selected_years), max(selected_years))
        else:
            year_range = (min_year, max_year)

    with col_b:
        sort_by = st.selectbox(
            "Sort by",
            ["Year (Newest)", "Year (Oldest)", "Title"],
            key="case_sort"
        )

if selected_years:
    filtered_df = df[df["year"].isin(selected_years)]
else:
    filtered_df = df

if search_term:
    filtered_df = filtered_df[
        filtered_df["title"].str.contains(search_term, case=False, na=False)
    ]

if sort_by == "Year (Newest)":
    filtered_df = filtered_df.sort_values("year", ascending=False)
elif sort_by == "Year (Oldest)":
    filtered_df = filtered_df.sort_values("year", ascending=True)
elif sort_by == "Title":
    filtered_df = filtered_df.sort_values("title")

st.subheader("Case Search Results")

if len(filtered_df) == 0:
    st.warning("No cases found matching your criteria.")
    st.stop()

st.write(f"Found {len(filtered_df)} cases")

col1, col2 = st.columns([2, 1])

with col1:
    display_count = st.slider("Cases to display", 10, 100, 25, key="case_display_count")

with col2:
    show_details = st.checkbox("Show case details", value=False, key="case_show_details")

st.dataframe(
    filtered_df[["year", "title", "court", "judge", "citation", "petitioner", "respondent",
                "decision_date", "disposal_nature", "author_judge", "case_id", "cnr",
                "available_languages", "description"]].head(display_count),
    use_container_width=True,
    column_config={
        "year": st.column_config.NumberColumn("Year", width="small"),
        "title": st.column_config.TextColumn("Case Title", width="large"),
        "court": st.column_config.TextColumn("Court", width="medium"),
        "judge": st.column_config.ListColumn("Judges", width="small"),
        "citation": st.column_config.ListColumn("Citations", width="small"),
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

if show_details and len(filtered_df) > 0:
    st.subheader("Case Details")

    case_options = [f"{row['year']} - {row['title'][:80]}..." for _, row in filtered_df.head(min(50, len(filtered_df))).iterrows()]

    selected_case = st.selectbox(
        "Select a case to view details",
        case_options,
        key="case_detail_select"
    )

    if selected_case:
        case_index = case_options.index(selected_case)
        case_data = filtered_df.iloc[case_index]

        col1, col2 = st.columns(2)

        with col1:
            st.write("### Case Information")
            st.write(f"**Year:** {case_data.get('year', 'N/A')}")
            st.write(f"**Title:** {case_data.get('title', 'N/A')}")
            st.write(f"**Court:** {case_data.get('court', 'N/A')}")

        with col2:
            st.write("### Judges")
            judges = case_data.get('judge', [])
            if isinstance(judges, list) and judges:
                for judge in judges:
                    st.write(f"• {judge}")
            else:
                st.write("No judges listed")

            st.write("### Citations")
            citations = case_data.get('citation', [])
            if isinstance(citations, list) and citations:
                for citation in citations:
                    st.write(f"• {citation}")
            else:
                st.write("No citations listed")

        if 'clean_text' in case_data and case_data['clean_text']:
            st.subheader("Case Summary")
            with st.expander("Show full case text"):
                st.write(case_data['clean_text'])

st.subheader("Quick Statistics")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Total Cases", len(filtered_df))

with col2:
    unique_judges = filtered_df.explode("judge")["judge"].nunique()
    st.metric("Unique Judges", unique_judges)

with col3:
    unique_citations = filtered_df.explode("citation")["citation"].nunique()
    st.metric("Unique Citations", unique_citations)

with col4:
    avg_judges = filtered_df["judge"].apply(lambda x: len(x) if isinstance(x, list) else 0).mean()
    st.metric("Avg Judges/Case", round(avg_judges, 1))

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