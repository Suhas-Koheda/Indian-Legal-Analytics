import streamlit as st
import pandas as pd
import altair as alt
from typing import Optional, List

def apply_theme():
    """Apply light/dark theme based on session state"""
    theme = st.session_state.get('theme', 'light')
    
    if theme == 'dark':
        st.markdown("""
        <style>
        .stApp {
            background-color: #0E1117;
            color: #FAFAFA;
        }
        .stMetric {
            background-color: #262730;
        }
        </style>
        """, unsafe_allow_html=True)

def render_theme_toggle():
    """Render theme toggle in sidebar"""
    current_theme = st.session_state.get('theme', 'light')
    
    if st.sidebar.button("🌙 Dark" if current_theme == 'light' else "☀️ Light"):
        st.session_state.theme = 'dark' if current_theme == 'light' else 'light'
        st.rerun()
    
    apply_theme()

def create_case_volume_chart(df: pd.DataFrame, title: str = "Case Volume Trends", height: int = 300) -> alt.Chart:
    """Create standardized case volume chart"""
    cases_per_year = (
        df.groupby("year")
        .size()
        .reset_index(name="case_count")
        .sort_values("year")
    )
    
    theme = st.session_state.get('theme', 'light')
    color = '#FF6B35' if theme == 'light' else '#4A9EFF'
    
    chart = alt.Chart(cases_per_year).mark_bar(opacity=0.8).encode(
        x=alt.X('year:O', title='Year'),
        y=alt.Y('case_count:Q', title='Number of Cases'),
        tooltip=['year', 'case_count'],
        color=alt.value(color)
    ).properties(
        title=title,
        height=height
    ).configure_axis(
        labelFontSize=11,
        titleFontSize=12,
        titleFontWeight='bold'
    ).configure_title(
        fontSize=14,
        fontWeight='bold'
    )
    
    return chart

def create_bar_chart(
    data: pd.DataFrame,
    x_col: str,
    y_col: str,
    title: str,
    height: int = 300,
    horizontal: bool = False
) -> alt.Chart:
    """Create standardized bar chart"""
    theme = st.session_state.get('theme', 'light')
    color = '#4CAF50' if theme == 'light' else '#66BB6A'
    
    if horizontal:
        chart = alt.Chart(data).mark_bar(opacity=0.9).encode(
            y=alt.Y(f'{x_col}:N', sort='-x', title=x_col),
            x=alt.X(f'{y_col}:Q', title=y_col),
            tooltip=[x_col, y_col],
            color=alt.value(color)
        )
    else:
        chart = alt.Chart(data).mark_bar(opacity=0.9).encode(
            x=alt.X(f'{x_col}:N', title=x_col),
            y=alt.Y(f'{y_col}:Q', title=y_col),
            tooltip=[x_col, y_col],
            color=alt.value(color)
        )
    
    chart = chart.properties(
        title=title,
        height=height
    ).configure_axis(
        labelFontSize=10,
        titleFontSize=11,
        titleFontWeight='bold'
    ).configure_title(
        fontSize=12,
        fontWeight='bold'
    )
    
    return chart

def create_line_chart(
    data: pd.DataFrame,
    x_col: str,
    y_col: str,
    color_col: Optional[str] = None,
    title: str = "",
    height: int = 300
) -> alt.Chart:
    """Create standardized line chart"""
    theme = st.session_state.get('theme', 'light')
    color = '#9C27B0' if theme == 'light' else '#BA68C8'
    
    encoding = {
        'x': alt.X(f'{x_col}:O', title=x_col),
        'y': alt.Y(f'{y_col}:Q', title=y_col),
        'tooltip': [x_col, y_col]
    }
    
    if color_col:
        encoding['color'] = alt.Color(f'{color_col}:N', title=color_col)
    else:
        encoding['color'] = alt.value(color)
    
    chart = alt.Chart(data).mark_line(point=True, size=3).encode(**encoding).properties(
        title=title,
        height=height
    ).configure_axis(
        labelFontSize=10,
        titleFontSize=11,
        titleFontWeight='bold'
    ).configure_title(
        fontSize=14,
        fontWeight='bold'
    )
    
    return chart

def render_year_filter(df: pd.DataFrame, key: str = "year_filter") -> List[int]:
    """Render year multiselect filter - no default selection"""
    min_year = int(df["year"].min()) if 'year' in df.columns else 1950
    max_year = int(df["year"].max()) if 'year' in df.columns else 2025
    years = list(range(min_year, max_year + 1))
    
    selected_years = st.multiselect(
        "Select Years",
        years,
        default=[],
        key=key
    )
    
    return selected_years

def render_search_bar(key: str = "search") -> str:
    """Render standardized search input"""
    return st.text_input("Search", "", key=key, placeholder="Search by case ID, title, parties, or citation")
