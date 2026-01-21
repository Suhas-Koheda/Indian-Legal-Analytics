import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(layout="wide")
st.title("⚖ Supreme Court Legal Analytics Dashboard")

df = pd.read_parquet("data/judgments.parquet")
