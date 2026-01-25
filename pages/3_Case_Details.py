import streamlit as st
import cache_utils
import aws_utils
import ui_components
import base64
from io import BytesIO

st.set_page_config(page_title="Case Details", layout="wide", initial_sidebar_state="collapsed")
st.title("📄 Case Details")

st.markdown("""
<style>
    .main .block-container {
        padding-left: 2rem;
        padding-right: 2rem;
        max-width: 100%;
    }
</style>
""", unsafe_allow_html=True)

ui_components.apply_theme()

if st.session_state.get('navigate_to_case_details'):
    year_from_explorer = st.session_state.get('case_details_year')
    case_id_from_explorer = st.session_state.get('case_details_case_id')
    
    if year_from_explorer and case_id_from_explorer:
        st.session_state['case_details_year'] = year_from_explorer
        st.session_state['case_details_case_id'] = case_id_from_explorer
        st.session_state['navigate_to_case_details'] = False
        
        with st.spinner("Fetching case details..."):
            case_data = cache_utils.get_case_details_cached(year_from_explorer, str(case_id_from_explorer).strip())
            
            if case_data:
                st.session_state['current_case'] = case_data
                st.success("Case loaded from Case Explorer!")
            else:
                st.error(f"Case not found for year {year_from_explorer} and case ID: {case_id_from_explorer}")

col1, col2 = st.columns([1, 1])

with col1:
    year = st.number_input(
        "Year",
        min_value=1950,
        max_value=2025,
        value=st.session_state.get('case_details_year', 2020),
        step=1,
        key="case_details_year"
    )

with col2:
    case_id = st.text_input(
        "Case ID",
        placeholder="Enter case ID",
        value=st.session_state.get('case_details_case_id', ''),
        key="case_details_case_id"
    )

if st.button("🔍 Fetch Case Details", type="primary"):
    if not case_id or not case_id.strip():
        st.error("Please enter a case ID")
        st.stop()
    
    with st.spinner("Fetching case details..."):
        case_id_input = case_id.strip()
        case_data = cache_utils.get_case_details_cached(year, case_id_input)
        
        if not case_data:
            st.warning(f"Case not found for year {year}. Trying to extract year from case ID...")
            case_data = cache_utils.get_case_details_cached(2025, case_id_input)
        
        if case_data:
            st.session_state['current_case'] = case_data
            actual_year = case_data.get('year', year)
            st.success(f"Case found! (Year: {actual_year})")
            if actual_year != year:
                st.info(f"⚠️ Note: Case was found in year {actual_year}, not {year}. Update the year field if needed.")
        else:
            st.error(f"Case not found. Please verify:\n- Year: {year}\n- Case ID: {case_id_input}\n\nTip: If the case ID contains a year (e.g., '2025 INSC 1401'), the year will be extracted automatically.")
            st.stop()

if 'current_case' in st.session_state:
    case = st.session_state['current_case']
    
    st.divider()
    st.subheader("Case Information")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown(f"**Title:** {case.get('title', 'N/A')}")
        st.markdown(f"**Year:** {case.get('year', 'N/A')}")
        st.markdown(f"**Court:** {case.get('court', 'N/A')}")
        st.markdown(f"**Case ID:** {case.get('case_id', 'N/A')}")
        st.markdown(f"**CNR:** {case.get('cnr', 'N/A')}")
    
    with col2:
        st.markdown(f"**Decision Date:** {case.get('decision_date', 'N/A')}")
        st.markdown(f"**Disposal Nature:** {case.get('disposal_nature', 'N/A')}")
        author_judge = case.get('author_judge', '')
        if isinstance(author_judge, list) and author_judge:
            st.markdown(f"**Author Judge:** {', '.join(author_judge)}")
        elif author_judge:
            st.markdown(f"**Author Judge:** {author_judge}")
        else:
            st.markdown("**Author Judge:** N/A")
    
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
        judges = case.get('judges', [])
        if isinstance(judges, list) and judges:
            for judge in judges:
                st.write(f"• {judge}")
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
    
    st.divider()
    st.subheader("📥 Download Judgment PDF")
    
    available_languages = case.get('available_languages', [])
    if not available_languages:
        available_languages = ['english']
    
    language = st.selectbox(
        "Select Language",
        available_languages,
        key="pdf_language"
    )
    
    actual_year = case.get('year', year)
    case_id_val = case.get('case_id', '')
    
    pdf_url = aws_utils.get_pdf_url(actual_year, case_id_val, language)
    
    if pdf_url:
        st.markdown("### 📎 PDF Location URL")
        st.code(pdf_url, language=None)
        st.markdown(f"**Note:** PDFs are stored in tar files. URL points to the tar archive containing this PDF.")
        print(f"\n{'='*80}")
        print(f"PDF URL for case {case_id_val} (year {actual_year}):")
        print(f"{pdf_url}")
        print(f"{'='*80}\n")
    
    if st.button("📄 Fetch PDF", type="primary"):
        with st.spinner(f"Downloading PDF (this may take a moment)..."):
            pdf_content = aws_utils.fetch_pdf_for_case(actual_year, case_id_val, language)
            
            if pdf_content:
                st.success("PDF downloaded successfully!")
                
                pdf_filename = f"{case_id_val}_{actual_year}.pdf"
                
                st.download_button(
                    label="⬇️ Download PDF",
                    data=pdf_content,
                    file_name=pdf_filename,
                    mime="application/pdf",
                    key="download_pdf"
                )
                
                st.markdown("---")
                st.subheader("PDF Preview")
                pdf_base64 = base64.b64encode(pdf_content).decode()
                st.markdown(f'<iframe src="data:application/pdf;base64,{pdf_base64}" width="100%" height="600px"></iframe>', unsafe_allow_html=True)
            else:
                st.error("Failed to fetch PDF. The file may not be available in the selected language or the path may be incorrect.")
                if pdf_url:
                    st.info(f"💡 Try accessing the PDF directly: {pdf_url}")

else:
    st.info("👆 Enter a year and case ID above to fetch case details, or select a case from Case Explorer page")
