import streamlit as st

st.set_page_config(
    page_title="⚖️ Legal Analytics Dashboard",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.sidebar.title("🧭 Navigation")
page = st.sidebar.radio(
    "Choose a page:",
    ["Overview", "Judge Analytics", "Case Explorer", "Citation Analytics", "Petitioner/Respondent", "Legal Chatbot"],
    help="Select a page to explore different aspects of the legal analytics dashboard",
    index=0
)

@st.cache_data(ttl=3600)  # Cache for 1 hour
def get_dashboard_stats():
    """Get basic dashboard statistics with caching"""
    try:
        import pandas as pd
        df = pd.read_parquet("data/base_for_dashboard.parquet")
        return {
            "total_cases": len(df),
            "year_range": f"{int(df['year'].min())} - {int(df['year'].max())}",
            "unique_judges": df.explode("judge")["judge"].nunique() if "judge" in df.columns else 0,
            "unique_citations": df.explode("citation")["citation"].nunique() if "citation" in df.columns else 0
        }
    except:
        return {"total_cases": 0, "year_range": "N/A", "unique_judges": 0, "unique_citations": 0}

stats = get_dashboard_stats()

st.sidebar.divider()
st.sidebar.markdown("### 📊 Dashboard Stats")
st.sidebar.metric("Total Cases", f"{stats['total_cases']:,}")
st.sidebar.metric("Year Range", stats['year_range'])
st.sidebar.metric("Unique Judges", f"{stats['unique_judges']:,}")
st.sidebar.metric("Unique Citations", f"{stats['unique_citations']:,}")

st.sidebar.divider()
st.sidebar.markdown("### 🏗️ Built With")
st.sidebar.markdown("- ⚖️ Streamlit")
st.sidebar.markdown("- 🤖 LangChain + Gemini AI")
st.sidebar.markdown("- 📊 Pandas & Matplotlib")

if st.sidebar.button("🔄 Clear All Cache"):
    st.cache_data.clear()
    st.cache_resource.clear()
    st.success("Cache cleared!")
    st.rerun()

if page == "Overview":
    exec(open("pages/1_Overview.py").read())
elif page == "Judge Analytics":
    exec(open("pages/2_Judge_Analytics.py").read())
elif page == "Case Explorer":
    exec(open("pages/4_Case_Explorer.py").read())
elif page == "Citation Analytics":
    exec(open("pages/5_Citations.py").read())
elif page == "Petitioner/Respondent":
    exec(open("pages/6_Petitioner_Respondent.py").read())
elif page == "Legal Chatbot":
    exec(open("pages/7_Chatbot.py").read())