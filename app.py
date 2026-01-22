import streamlit as st

st.set_page_config(
    page_title="Legal Analytics Dashboard",
    layout="wide"
)

st.sidebar.title("Navigation")
page = st.sidebar.radio(
    "Choose a page:",
    ["Overview", "Judge Analytics", "Article Analytics", "Case Explorer", "Citation Analytics"]
)

if page == "Overview":
    exec(open("pages/1_Overview.py").read())
elif page == "Judge Analytics":
    exec(open("pages/2_Judge_Analytics.py").read())
elif page == "Article Analytics":
    exec(open("pages/3_Article_Analytics.py").read())
elif page == "Case Explorer":
    exec(open("pages/4_Case_Explorer.py").read())
elif page == "Citation Analytics":
    exec(open("pages/5_Citations.py").read())