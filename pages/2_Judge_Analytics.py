import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(
    page_title="Judge Analytics | Legal Analytics Dashboard",
    layout="wide"
)

st.title("Judge Analytics")

@st.cache_data
def load_data():
    return pd.read_parquet("data/base_for_dashboard.parquet")

df = load_data()

def normalize_judge_value(val):
    if isinstance(val, list):
        return val

    if val is None or (isinstance(val, float) and pd.isna(val)):
        return []

    if isinstance(val, str):
        return [v.strip() for v in val.split(",") if v.strip()]

    return []

df["judge"] = df["judge"].apply(normalize_judge_value)

st.sidebar.header("Filters")

min_year = int(df["year"].min())
max_year = int(df["year"].max())

year_range = st.sidebar.slider(
    "Select Year Range",
    min_year,
    max_year,
    (min_year, max_year)
)

filtered_df = df[
    (df["year"] >= year_range[0]) &
    (df["year"] <= year_range[1])
]

all_judges = (
    filtered_df
    .explode("judge")["judge"]
    .dropna()
    .sort_values()
    .unique()
)

if len(all_judges) == 0:
    st.warning("No judges found for the selected year range.")
    st.stop()

selected_judge = st.sidebar.selectbox(
    "Select Judge",
    all_judges
)

judge_df = filtered_df[
    filtered_df["judge"].apply(lambda lst: selected_judge in lst)
]

st.subheader(f"Justice {selected_judge}")

c1, c2, c3 = st.columns(3)

with c1:
    st.metric("Total Cases", len(judge_df))

with c2:
    st.metric("Years Active", judge_df["year"].nunique())

with c3:
    avg = len(judge_df) / max(judge_df["year"].nunique(), 1)
    st.metric("Avg Cases / Year", round(avg, 2))

st.subheader("Year-wise Case Load")

cases_per_year = (
    judge_df.groupby("year")
    .size()
    .reset_index(name="case_count")
    .sort_values("year")
)

fig, ax = plt.subplots()
ax.plot(cases_per_year["year"], cases_per_year["case_count"])
ax.set_xlabel("Year")
ax.set_ylabel("Number of Cases")
ax.set_title(f"Cases handled by {selected_judge}")

st.pyplot(fig)

st.subheader("Sample Cases")

st.dataframe(
    judge_df[["year", "title", "court"]].head(25),
    use_container_width=True
)
