import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

st.title("Petitioner vs Respondent Analytics")

@st.cache_data
def load_data():
    return pd.read_parquet("data/base_for_dashboard.parquet")

df = load_data()

col1, col2, col3, col4 = st.columns([2, 1, 1, 1])

with col1:
    search_term = st.text_input("Search parties", "", key="party_search")

with col2:
    min_year = int(df["year"].min())
    max_year = int(df["year"].max())
    years = list(range(min_year, max_year + 1))
    selected_years = st.multiselect(
        "Select Years",
        years,
        default=[min_year, max_year],
        key="party_years"
    )

with col3:
    if selected_years:
        year_range = (min(selected_years), max(selected_years))
    else:
        year_range = (min_year, max_year)

with col4:
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
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Petitioners by Year")

        petitioner_trends = (
            filtered_df
            .explode("petitioner")
            .dropna(subset=["petitioner"])
            .groupby(["year", "petitioner"])
            .size()
            .reset_index(name="count")
            .sort_values(["year", "count"], ascending=[True, False])
            .groupby("year")
            .head(1)
        )

        fig, ax = plt.subplots(figsize=(6, 4))
        for petitioner in petitioner_trends["petitioner"].unique()[:5]:
            data = petitioner_trends[petitioner_trends["petitioner"] == petitioner]
            ax.plot(data["year"], data["count"], marker='o', label=petitioner[:20])

        ax.set_xlabel("Year")
        ax.set_ylabel("Cases")
        ax.set_title("Top Petitioner Trends")
        ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')

        st.pyplot(fig)

    with col2:
        st.subheader("Respondents by Year")

        respondent_trends = (
            filtered_df
            .explode("respondent")
            .dropna(subset=["respondent"])
            .groupby(["year", "respondent"])
            .size()
            .reset_index(name="count")
            .sort_values(["year", "count"], ascending=[True, False])
            .groupby("year")
            .head(1)
        )

        fig, ax = plt.subplots(figsize=(6, 4))
        for respondent in respondent_trends["respondent"].unique()[:5]:
            data = respondent_trends[respondent_trends["respondent"] == respondent]
            ax.plot(data["year"], data["count"], marker='s', label=respondent[:20])

        ax.set_xlabel("Year")
        ax.set_ylabel("Cases")
        ax.set_title("Top Respondent Trends")
        ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')

        st.pyplot(fig)

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
        party_df.head(50),
        use_container_width=True,
        column_config={
            "party": st.column_config.TextColumn("Party Name", width="medium"),
            "role": st.column_config.TextColumn("Role", width="small"),
            "year": st.column_config.NumberColumn("Year", width="small"),
            "title": st.column_config.TextColumn("Case Title", width="large")
        }
    )

st.subheader("Party Distribution by Role")

role_counts = []
petitioner_count = sum(filtered_df["petitioner"].apply(lambda x: len(x) if isinstance(x, list) else 0))
respondent_count = sum(filtered_df["respondent"].apply(lambda x: len(x) if isinstance(x, list) else 0))

fig, ax = plt.subplots(figsize=(8, 4))
ax.bar(["Petitioners", "Respondents"], [petitioner_count, respondent_count], color=['lightblue', 'lightcoral'])
ax.set_ylabel("Total Party Mentions")
ax.set_title("Petitioner vs Respondent Distribution")

for i, v in enumerate([petitioner_count, respondent_count]):
    ax.text(i, v + 5, str(v), ha='center', va='bottom')

st.pyplot(fig)