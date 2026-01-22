import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import altair as alt

st.title("Petitioner vs Respondent Analytics")

@st.cache_data
def load_data():
    return pd.read_parquet("data/base_for_dashboard.parquet")

df = load_data()

col1, col2 = st.columns([3, 2])

with col1:
    search_term = st.text_input("Search parties", "", key="party_search")

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
            key="party_years"
        )

        if selected_years:
            year_range = (min(selected_years), max(selected_years))
        else:
            year_range = (min_year, max_year)

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
    filtered_df = filtered_df[
        filtered_df["petitioner"].apply(
            lambda lst: any(search_term.lower() in str(p).lower() for p in lst) if isinstance(lst, list) else False
        ) |
        filtered_df["respondent"].apply(
            lambda lst: any(search_term.lower() in str(r).lower() for r in lst) if isinstance(lst, list) else False
        )
    ]

st.subheader("Party Analysis Summary")

c1, c2, c3, c4 = st.columns(4)

with c1:
    st.metric("Total Cases", len(filtered_df))

with c2:
    unique_petitioners = filtered_df.explode("petitioner")["petitioner"].nunique()
    st.metric("Unique Petitioners", unique_petitioners)

with c3:
    unique_respondents = filtered_df.explode("respondent")["respondent"].nunique()
    st.metric("Unique Respondents", unique_respondents)

with c4:
    avg_petitioners = filtered_df["petitioner"].apply(lambda x: len(x) if isinstance(x, list) else 0).mean()
    st.metric("Avg Petitioners/Case", round(avg_petitioners, 1))

if analysis_type in ["Petitioners", "Both"]:
    st.subheader("Top Petitioners by Case Volume")

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

    fig, ax = plt.subplots(figsize=(8, 6))
    bars = ax.barh(top_petitioners["petitioner"], top_petitioners["case_count"], color='lightblue')
    ax.invert_yaxis()
    ax.set_xlabel("Number of Cases")
    ax.set_title("Most Active Petitioners")

    st.pyplot(fig)

if analysis_type in ["Respondents", "Both"]:
    st.subheader("Top Respondents by Case Volume")

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

    fig, ax = plt.subplots(figsize=(8, 6))
    bars = ax.barh(top_respondents["respondent"], top_respondents["case_count"], color='lightcoral')
    ax.invert_yaxis()
    ax.set_xlabel("Number of Cases")
    ax.set_title("Most Frequent Respondents")

    st.pyplot(fig)

if analysis_type == "Both":
    cols = st.columns(2, gap="medium")

    with cols[0].container(border=True, height=350):
        st.subheader("🗣️ Top Petitioners by Year")

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

        petitioner_chart = alt.Chart(petitioner_trends.head(50)).mark_line(point=True).encode(
            x=alt.X('year:O', title='Year'),
            y=alt.Y('count:Q', title='Cases'),
            color=alt.Color('petitioner:N', title='Petitioner'),
            tooltip=['year', 'petitioner', 'count']
        ).properties(
            title='Top Petitioner Trends Over Time',
            height=280
        )

        st.altair_chart(petitioner_chart, use_container_width=True)

    with cols[1].container(border=True, height=350):
        st.subheader("🛡️ Top Respondents by Year")

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

        respondent_chart = alt.Chart(respondent_trends.head(50)).mark_line(point=True).encode(
            x=alt.X('year:O', title='Year'),
            y=alt.Y('count:Q', title='Cases'),
            color=alt.Color('respondent:N', title='Respondent'),
            tooltip=['year', 'respondent', 'count']
        ).properties(
            title='Top Respondent Trends Over Time',
            height=280
        )

        st.altair_chart(respondent_chart, use_container_width=True)

st.subheader("Detailed Party Analysis")

party_stats = []

for _, row in filtered_df.iterrows():
    petitioners = row.get("petitioner", []) if isinstance(row.get("petitioner"), list) else []
    respondents = row.get("respondent", []) if isinstance(row.get("respondent"), list) else []

    for petitioner in petitioners:
        party_stats.append({
            "party": petitioner,
            "role": "Petitioner",
            "year": row["year"],
            "title": row["title"]
        })

    for respondent in respondents:
        party_stats.append({
            "party": respondent,
            "role": "Respondent",
            "year": row["year"],
            "title": row["title"]
        })

if party_stats:
    party_df = pd.DataFrame(party_stats)

st.dataframe(
    filtered_df[["year", "title", "court", "judge", "citation", "petitioner", "respondent", "decision_date", "disposal_nature"]].head(50),
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
        "disposal_nature": st.column_config.TextColumn("Disposal Nature", width="small")
    }
)

st.subheader("⚖️ Party Distribution by Role")

petitioner_count = sum(filtered_df["petitioner"].apply(lambda x: len(x) if isinstance(x, list) else 0))
respondent_count = sum(filtered_df["respondent"].apply(lambda x: len(x) if isinstance(x, list) else 0))

party_data = pd.DataFrame({
    'role': ['Petitioners', 'Respondents'],
    'count': [petitioner_count, respondent_count]
})

party_chart = alt.Chart(party_data).mark_bar(size=60).encode(
    x=alt.X('role:N', title='Role'),
    y=alt.Y('count:Q', title='Total Party Mentions'),
    color=alt.Color('role:N', scale=alt.Scale(domain=['Petitioners', 'Respondents'],
                                             range=['#2196F3', '#F44336'])),
    tooltip=['role', 'count']
).properties(
    title='Petitioner vs Respondent Distribution',
    height=300
).configure_axis(
    labelFontSize=11,
    titleFontSize=12,
    titleFontWeight='bold'
).configure_title(
    fontSize=14,
    fontWeight='bold'
)

st.altair_chart(party_chart, use_container_width=True)

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