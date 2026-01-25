import streamlit as st
import pandas as pd
import cache_utils
import ui_components

st.title("Petitioner vs Respondent Analytics")

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

col1, col2 = st.columns([3, 2])

with col1:
    search_term = ui_components.render_search_bar("party_search")

with col2:
    col_a, col_b = st.columns([3, 2])

    with col_a:
        selected_years = ui_components.render_year_filter(df, "party_years")

    with col_b:
        analysis_type = st.selectbox(
            "Analysis Type",
            ["Petitioners", "Respondents", "Both"],
            key="party_analysis_type"
        )

if selected_years:
    filtered_df = df[df["year"].isin(selected_years)]
else:
    filtered_df = df

if search_term:
    has_petitioner = False
    has_respondent = False
    
    if 'petitioner' in filtered_df.columns:
        has_petitioner = filtered_df["petitioner"].apply(
            lambda lst: any(search_term.lower() in str(p).lower() for p in lst) if isinstance(lst, list) else search_term.lower() in str(lst).lower()
        )
    
    if 'respondent' in filtered_df.columns:
        has_respondent = filtered_df["respondent"].apply(
            lambda lst: any(search_term.lower() in str(r).lower() for r in lst) if isinstance(lst, list) else search_term.lower() in str(lst).lower()
        )
    
    filtered_df = filtered_df[has_petitioner | has_respondent]

st.subheader("Party Analysis Summary")

c1, c2, c3, c4 = st.columns(4)

with c1:
    st.metric("Total Cases", len(filtered_df))

with c2:
    if 'petitioner' in filtered_df.columns:
        try:
            unique_petitioners = filtered_df.explode("petitioner")["petitioner"].nunique()
            st.metric("Unique Petitioners", unique_petitioners)
        except:
            st.metric("Unique Petitioners", "N/A")
    else:
        st.metric("Unique Petitioners", "N/A")

with c3:
    if 'respondent' in filtered_df.columns:
        try:
            unique_respondents = filtered_df.explode("respondent")["respondent"].nunique()
            st.metric("Unique Respondents", unique_respondents)
        except:
            st.metric("Unique Respondents", "N/A")
    else:
        st.metric("Unique Respondents", "N/A")

with c4:
    if 'petitioner' in filtered_df.columns:
        try:
            avg_petitioners = filtered_df["petitioner"].apply(lambda x: len(x) if isinstance(x, list) else 0).mean()
            st.metric("Avg Petitioners/Case", round(avg_petitioners, 1))
        except:
            st.metric("Avg Petitioners/Case", "N/A")
    else:
        st.metric("Avg Petitioners/Case", "N/A")

if analysis_type in ["Petitioners", "Both"]:
    st.subheader("Top Petitioners by Case Volume")

    if 'petitioner' in filtered_df.columns:
        top_petitioners = (
            filtered_df
            .explode("petitioner")
            .dropna(subset=["petitioner"])
            .groupby("petitioner")
            .size()
            .reset_index(name="case_count")
            .sort_values("case_count", ascending=False)
            .head(15)
        )

        if len(top_petitioners) > 0:
            petitioner_chart = ui_components.create_bar_chart(
                top_petitioners,
                'petitioner',
                'case_count',
                'Most Active Petitioners',
                height=400,
                horizontal=True
            )
            st.altair_chart(petitioner_chart, width='stretch')
        else:
            st.info("No petitioner data available")
    else:
        st.info("Petitioner data not available")

if analysis_type in ["Respondents", "Both"]:
    st.subheader("Top Respondents by Case Volume")

    if 'respondent' in filtered_df.columns:
        top_respondents = (
            filtered_df
            .explode("respondent")
            .dropna(subset=["respondent"])
            .groupby("respondent")
            .size()
            .reset_index(name="case_count")
            .sort_values("case_count", ascending=False)
            .head(15)
        )

        if len(top_respondents) > 0:
            respondent_chart = ui_components.create_bar_chart(
                top_respondents,
                'respondent',
                'case_count',
                'Most Frequent Respondents',
                height=400,
                horizontal=True
            )
            st.altair_chart(respondent_chart, width='stretch')
        else:
            st.info("No respondent data available")
    else:
        st.info("Respondent data not available")

if analysis_type == "Both":
    cols = st.columns(2, gap="medium")

    with cols[0].container(border=True, height=350):
        st.subheader("🗣️ Top Petitioners by Year")

        if 'petitioner' in filtered_df.columns:
            petitioner_trends = (
                filtered_df
                .explode("petitioner")
                .dropna(subset=["petitioner"])
                .groupby(["year", "petitioner"])
                .size()
                .reset_index(name="count")
                .sort_values(["year", "count"], ascending=[True, False])
                .groupby("year")
                .head(3)
            )

            if len(petitioner_trends) > 0:
                petitioner_trend_chart = ui_components.create_line_chart(
                    petitioner_trends.head(50),
                    'year',
                    'count',
                    color_col='petitioner',
                    title='Top Petitioner Trends Over Time',
                    height=280
                )
                st.altair_chart(petitioner_trend_chart, width='stretch')
            else:
                st.info("No petitioner trend data available")
        else:
            st.info("Petitioner data not available")

    with cols[1].container(border=True, height=350):
        st.subheader("🛡️ Top Respondents by Year")

        if 'respondent' in filtered_df.columns:
            respondent_trends = (
                filtered_df
                .explode("respondent")
                .dropna(subset=["respondent"])
                .groupby(["year", "respondent"])
                .size()
                .reset_index(name="count")
                .sort_values(["year", "count"], ascending=[True, False])
                .groupby("year")
                .head(3)
            )

            if len(respondent_trends) > 0:
                respondent_trend_chart = ui_components.create_line_chart(
                    respondent_trends.head(50),
                    'year',
                    'count',
                    color_col='respondent',
                    title='Top Respondent Trends Over Time',
                    height=280
                )
                st.altair_chart(respondent_trend_chart, width='stretch')
            else:
                st.info("No respondent trend data available")
        else:
            st.info("Respondent data not available")

st.subheader("Detailed Party Analysis")

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

col_config = {}
for col in display_cols:
    if col == "year":
        col_config[col] = st.column_config.NumberColumn("Year", width="small")
    elif col == "title":
        col_config[col] = st.column_config.TextColumn("Case Title", width="large")
    elif col in ["judge", "citation", "petitioner", "respondent"]:
        col_config[col] = st.column_config.ListColumn(col.title(), width="small")
    else:
        col_config[col] = st.column_config.TextColumn(col.replace("_", " ").title(), width="medium")

st.dataframe(
    filtered_df[display_cols].head(50),
    width='stretch',
    column_config=col_config
)

st.subheader("⚖️ Party Distribution by Role")

if 'petitioner' in filtered_df.columns and 'respondent' in filtered_df.columns:
    try:
        petitioner_count = sum(filtered_df["petitioner"].apply(lambda x: len(x) if isinstance(x, list) else 0))
        respondent_count = sum(filtered_df["respondent"].apply(lambda x: len(x) if isinstance(x, list) else 0))

        party_data = pd.DataFrame({
            'role': ['Petitioners', 'Respondents'],
            'count': [petitioner_count, respondent_count]
        })

        party_chart = ui_components.create_bar_chart(
            party_data,
            'role',
            'count',
            'Petitioner vs Respondent Distribution',
            height=300
        )

        st.altair_chart(party_chart, width='stretch')
    except:
        st.info("Unable to calculate party distribution")
else:
    st.info("Party data not available for distribution analysis")

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
