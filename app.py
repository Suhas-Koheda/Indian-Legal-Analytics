import streamlit as st
import cache_utils
import ui_components

st.set_page_config(
    page_title="⚖️ Legal Analytics Dashboard",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .main .block-container {
        padding-left: 2rem;
        padding-right: 2rem;
        max-width: 100%;
    }
</style>
""", unsafe_allow_html=True)

st.session_state.setdefault('theme', 'light')

ui_components.apply_theme()

st.sidebar.title("🧭 Navigation")

page = st.sidebar.radio(
    "Choose a page:",
    ["Overview", "Case Details", "Judge Analytics", "Case Explorer", "Citation Analytics", "Petitioner/Respondent", "Legal Chatbot"],
    help="Select a page to explore different aspects of the legal analytics dashboard",
    index=0
)

@st.cache_data(ttl=3600)
def get_dashboard_stats():
    """
    Get basic dashboard statistics with caching.
    Uses cache_utils to fetch from S3 instead of local files.
    TTL: 1 hour - stats don't change frequently.
    Using st.cache_data because return value is serializable dict.
    """
    try:
        df = cache_utils.get_combined_metadata()
        if df is None or len(df) == 0:
            return {"total_cases": 0, "year_range": "N/A", "unique_judges": 0, "unique_citations": 0}
        
        judge_col = 'judge' if 'judge' in df.columns else None
        citation_col = 'citation' if 'citation' in df.columns else None
        
        unique_judges = 0
        unique_citations = 0
        
        if judge_col:
            try:
                unique_judges = df.explode("judge")["judge"].nunique()
            except:
                pass
        
        if citation_col:
            try:
                unique_citations = df.explode("citation")["citation"].nunique()
            except:
                pass
        
        return {
            "total_cases": len(df),
            "year_range": f"{int(df['year'].min())} - {int(df['year'].max())}",
            "unique_judges": unique_judges,
            "unique_citations": unique_citations
        }
    except Exception as e:
        return {"total_cases": 0, "year_range": "N/A", "unique_judges": 0, "unique_citations": 0}

stats = get_dashboard_stats()

st.sidebar.divider()
st.sidebar.markdown("### 📊 Dashboard Stats")
st.sidebar.metric("Total Cases", f"{stats['total_cases']:,}")
st.sidebar.metric("Year Range", stats['year_range'])
st.sidebar.metric("Unique Judges", f"{stats['unique_judges']:,}")
st.sidebar.metric("Unique Citations", f"{stats['unique_citations']:,}")

st.sidebar.divider()
ui_components.render_theme_toggle()

st.sidebar.divider()
st.sidebar.markdown("### 🏗️ Built With")
st.sidebar.markdown("- ⚖️ Streamlit")
st.sidebar.markdown("- 🤖 LangChain + Gemini AI")
st.sidebar.markdown("- 📊 Pandas & Altair")
st.sidebar.markdown("- ☁️ AWS S3")

if st.sidebar.button("🔄 Clear All Cache"):
    st.cache_data.clear()
    st.cache_resource.clear()
    st.success("Cache cleared!")
    st.rerun()

import importlib.util
import sys

page_modules = {
    "Overview": "pages/1_Overview.py",
    "Case Details": "pages/3_Case_Details.py",
    "Judge Analytics": "pages/2_Judge_Analytics.py",
    "Case Explorer": "pages/4_Case_Explorer.py",
    "Citation Analytics": "pages/5_Citations.py",
    "Petitioner/Respondent": "pages/6_Petitioner_Respondent.py",
    "Legal Chatbot": "pages/7_Chatbot.py"
}

if page in page_modules:
    page_path = page_modules[page]
    spec = importlib.util.spec_from_file_location("page_module", page_path)
    if spec and spec.loader:
        page_module = importlib.util.module_from_spec(spec)
        sys.modules["page_module"] = page_module
        spec.loader.exec_module(page_module)
