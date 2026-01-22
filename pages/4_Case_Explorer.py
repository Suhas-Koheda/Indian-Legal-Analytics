import streamlit as st
import pandas as pd

st.set_page_config(
    page_title="Case Explorer | Legal Analytics Dashboard",
    layout="wide"
)

st.title("Case Explorer")

@st.cache_data
def load_data():
    return pd.read_parquet("data/base_for_dashboard.parquet")

df = load_data()

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

search_term = st.sidebar.text_input("Search in case titles", "")

if search_term:
    filtered_df = filtered_df[
        filtered_df["title"].str.contains(search_term, case=False, na=False)
    ]

st.subheader("Case Search Results")

if len(filtered_df) == 0:
    st.warning("No cases found matching your criteria.")
else:
    st.write(f"Found {len(filtered_df)} cases")

    display_cols = ["year", "title", "court"]
    available_cols = [c for c in display_cols if c in filtered_df.columns]

    st.dataframe(
        filtered_df[available_cols].head(50),
        use_container_width=True
    )

    st.subheader("Case Details")

    if len(filtered_df) > 0:
        case_options = [f"{row['year']} - {row['title'][:100]}..." for _, row in filtered_df.head(100).iterrows()]

        selected_case = st.selectbox(
            "Select a case to view details",
            case_options
        )

        if selected_case:
            case_index = case_options.index(selected_case)
            case_data = filtered_df.iloc[case_index]

            col1, col2 = st.columns(2)

            with col1:
                st.write("**Case Information:**")
                st.write(f"**Year:** {case_data.get('year', 'N/A')}")
                st.write(f"**Title:** {case_data.get('title', 'N/A')}")
                st.write(f"**Court:** {case_data.get('court', 'N/A')}")

            with col2:
                st.write("**Judges:**")
                judges = case_data.get('judge', [])
                if isinstance(judges, list) and judges:
                    for judge in judges:
                        st.write(f"- {judge}")
                else:
                    st.write("No judges listed")

                st.write("**Legal Provisions:**")
                provisions = case_data.get('legal_provisions', [])
                if isinstance(provisions, list) and provisions:
                    for provision in provisions:
                        st.write(f"- {provision}")
                else:
                    st.write("No legal provisions listed")

            if 'clean_text' in case_data and case_data['clean_text']:
                st.subheader("Case Summary")
                summary = case_data['clean_text'][:1000] + "..." if len(str(case_data['clean_text'])) > 1000 else case_data['clean_text']
                st.write(summary)