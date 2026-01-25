import streamlit as st
import pandas as pd
import cache_utils
import search
import ui_components
import aws_utils
import base64

st.set_page_config(layout="wide")
st.title("Case Explorer")

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
    search_term = ui_components.render_search_bar("case_search")

with col2:
    col_a, col_b = st.columns([3, 2])

    with col_a:
        selected_years = ui_components.render_year_filter(df, "case_years")

    with col_b:
        sort_by = st.selectbox(
            "Sort by",
            ["Year (Newest)", "Year (Oldest)", "Title", "Relevance"],
            key="case_sort"
        )

if selected_years:
    filtered_df = df[df["year"].isin(selected_years)].copy()
else:
    filtered_df = df.copy()

if search_term and search_term.strip():
    search_results = search.search_cases(filtered_df, search_term.strip())
    
    if len(search_results) == 0:
        st.warning(f"No cases found matching '{search_term}'")
        st.stop()
    
    filtered_df = search_results.reset_index(drop=True)
    
    if sort_by == "Relevance" and '_search_score' in filtered_df.columns:
        filtered_df = filtered_df.sort_values(['_search_score', 'year'], ascending=[False, False])
    elif sort_by == "Relevance":
        sort_by = "Year (Newest)"

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

if search_term and '_match_type' in filtered_df.columns:
    exact_matches = len(filtered_df[filtered_df['_match_type'] == 'exact'])
    partial_matches = len(filtered_df[filtered_df['_match_type'] == 'partial'])
    contains_matches = len(filtered_df[filtered_df['_match_type'] == 'contains'])
    
    match_info = []
    if exact_matches > 0:
        match_info.append(f"{exact_matches} exact")
    if partial_matches > 0:
        match_info.append(f"{partial_matches} partial")
    if contains_matches > 0:
        match_info.append(f"{contains_matches} contains")
    
    if match_info:
        st.info(f"📊 Search results: {', '.join(match_info)} match(es)")

col1, col2 = st.columns([2, 1])

with col1:
    display_count = st.slider("Cases to display", 10, 100, 25, key="case_display_count")

with col2:
    show_details = st.checkbox("Show case details", value=True, key="case_show_details")

display_cols = ["year", "title", "court"]
optional_cols = ["judge", "citation", "petitioner", "respondent", "decision_date", "disposal_nature", "case_id"]

for col in optional_cols:
    if col in filtered_df.columns:
        display_cols.append(col)

available_display_cols = [col for col in display_cols if col in filtered_df.columns]

if not available_display_cols:
    st.error("No displayable columns found in the results.")
    st.stop()

display_df = filtered_df[available_display_cols].head(display_count).copy()

if '_search_score' in display_df.columns:
    display_df = display_df.drop(columns=['_search_score'], errors='ignore')
if '_match_type' in display_df.columns:
    display_df = display_df.drop(columns=['_match_type'], errors='ignore')

col_config = {}
for col in available_display_cols:
    if col not in display_df.columns:
        continue
    if col == "year":
        col_config[col] = st.column_config.NumberColumn("Year", width="small")
    elif col == "title":
        col_config[col] = st.column_config.TextColumn("Case Title", width="large")
    elif col in ["judge", "citation", "petitioner", "respondent"]:
        col_config[col] = st.column_config.ListColumn(col.title(), width="small")
    else:
        col_config[col] = st.column_config.TextColumn(col.replace("_", " ").title(), width="medium")

if len(display_df) > 0:
    st.dataframe(display_df, width='stretch', column_config=col_config)
else:
    st.warning("No cases to display. Try adjusting your search or filters.")

if show_details and len(filtered_df) > 0:
    st.divider()
    st.subheader("📄 Case Details & Metadata Summary")

    case_options = ["Select a case..."] + [f"{row['year']} - {row['title'][:80]}..." for _, row in filtered_df.head(min(50, len(filtered_df))).iterrows()]

    selected_case = st.selectbox(
        "Select a case to view full details",
        case_options,
        key="case_detail_select"
    )

    if selected_case and selected_case != "Select a case...":
        case_index = case_options.index(selected_case) - 1
        # Get basic info from the dataframe row
        row_data = filtered_df.iloc[case_index]
        
        selected_year = int(row_data.get('year', 0))
        selected_case_id = str(row_data.get('case_id', ''))
        
        # Use local metadata for instant display instead of re-fetching from AWS
        case = row_data.to_dict()
        
        # Ensure list fields are lists (sometimes pandas Series to_dict behaves oddly with lists)
        # But since we normalized them in cache_utils, they should be fine.
        
        # We NO LONGER call cache_utils.get_case_details_cached(selected_year, selected_case_id) here
        # to satisfy "use metadata only" for display.
        
        # if not case:
        #      # Fallback to row data if cache fetch fails
        #      case = row_data.to_dict()
        
        st.markdown("---")
        
        # Header with Title and Year
        st.markdown(f"### {case.get('title', 'N/A')}")
        
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.markdown(f"**Year:** {case.get('year', 'N/A')}")
            st.markdown(f"**Court:** {case.get('court', 'N/A')}")
            st.markdown(f"**Case ID:** {case.get('case_id', 'N/A')}")
            if case.get('cnr'):
                st.markdown(f"**CNR:** {case.get('cnr', 'N/A')}")
        
        with col2:
            st.markdown(f"**Decision Date:** {case.get('decision_date', 'N/A')}")
            st.markdown(f"**Disposal Nature:** {case.get('disposal_nature', 'N/A')}")
            author_judge = case.get('author_judge', '')
            if isinstance(author_judge, list) and author_judge:
                st.markdown(f"**Author Judge:** {', '.join(author_judge)}")
            elif author_judge:
                st.markdown(f"**Author Judge:** {author_judge}")
        
        st.divider()
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Petitioner")
            petitioner = case.get('petitioner', '')
            if isinstance(petitioner, list):
                if petitioner:
                    for p in petitioner:
                        st.write(f"• {p}")
                else:
                    st.write("N/A")
            else:
                st.write(petitioner if petitioner else "N/A")
        
        with col2:
            st.subheader("Respondent")
            respondent = case.get('respondent', '')
            if isinstance(respondent, list):
                if respondent:
                    for r in respondent:
                        st.write(f"• {r}")
                else:
                    st.write("N/A")
            else:
                st.write(respondent if respondent else "N/A")
        
        st.divider()
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Judges")
            judges = case.get('judge', case.get('judges', []))
            if isinstance(judges, list) and judges:
                for judge in judges:
                    if str(judge).strip():
                        st.write(f"• {judge}")
            elif isinstance(judges, str) and judges.strip():
                 st.write(f"• {judges}")
            else:
                st.write("N/A")
        
        with col2:
            st.subheader("Citations")
            citations = case.get('citation', [])
            if isinstance(citations, list) and citations:
                for citation in citations:
                    st.write(f"• {citation}")
            else:
                st.write("N/A")
        
        if case.get('description'):
            st.divider()
            st.subheader("Description")
            st.write(case['description'])
            
        # PDF DOWNLOAD SECTION
        st.divider()
        st.subheader("📥 Judgment Document")
        
        # Check available languages
        available_languages = case.get('available_languages', [])
        if not available_languages:
            available_languages = ['english']
        
        col_pdf_1, col_pdf_2 = st.columns([1, 2])
        
        with col_pdf_1:
            language = st.selectbox(
                "Select Language",
                available_languages,
                key=f"pdf_lang_{case_index}"
            )
            
            fetch_btn = st.button("📄 Fetch Full Judgment PDF", key=f"fetch_pdf_{case_index}", type="primary")

        with col_pdf_2:
            if fetch_btn:
                actual_year = case.get('year', selected_year)
                case_id_val = case.get('case_id', selected_case_id)
                
                with st.spinner(f"Downloading PDF (this may take a moment)..."):
                    try:
                        # Get path from local metadata to avoid re-fetching from AWS
                        pdf_path = case.get('path', None)
                        pdf_content = aws_utils.fetch_pdf_for_case(actual_year, case_id_val, language, pdf_path=pdf_path)
                        
                        if pdf_content:
                            st.success("PDF downloaded!")
                            pdf_filename = f"{str(case_id_val).replace(' ', '_')}_{actual_year}.pdf"
                            
                            st.download_button(
                                label="⬇️ Download PDF",
                                data=pdf_content,
                                file_name=pdf_filename,
                                mime="application/pdf",
                                key=f"dl_btn_{case_index}"
                            )
                            
                            # Preview
                            pdf_base64 = base64.b64encode(pdf_content).decode()
                            st.markdown(f'<iframe src="data:application/pdf;base64,{pdf_base64}" width="100%" height="600px"></iframe>', unsafe_allow_html=True)
                        else:
                            st.error("Failed to fetch PDF. It might be missing in the archive.")
                            pdf_url = aws_utils.get_pdf_url(actual_year, case_id_val, language)
                            if pdf_url:
                                st.info(f"Source URL: {pdf_url}")
                    except Exception as e:
                        st.error(f"Error fetching PDF: {str(e)}")

st.subheader("Quick Statistics")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Total Cases", len(filtered_df))

with col2:
    if 'judge' in filtered_df.columns:
        try:
            unique_judges = filtered_df.explode("judge")["judge"].nunique()
            st.metric("Unique Judges", unique_judges)
        except:
            st.metric("Unique Judges", "N/A")
    else:
        st.metric("Unique Judges", "N/A")

with col3:
    if 'citation' in filtered_df.columns:
        try:
            unique_citations = filtered_df.explode("citation")["citation"].nunique()
            st.metric("Unique Citations", unique_citations)
        except:
            st.metric("Unique Citations", "N/A")
    else:
        st.metric("Unique Citations", "N/A")

with col4:
    if 'judge' in filtered_df.columns:
        try:
            avg_judges = filtered_df["judge"].apply(lambda x: len(x) if isinstance(x, list) else 0).mean()
            st.metric("Avg Judges/Case", round(avg_judges, 1))
        except:
            st.metric("Avg Judges/Case", "N/A")
    else:
        st.metric("Avg Judges/Case", "N/A")

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
