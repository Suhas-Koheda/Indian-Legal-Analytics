import streamlit as st
import pandas as pd
from typing import Optional, Dict, List
import aws_utils

@st.cache_data(ttl=3600)
def get_metadata_for_year(year: int) -> Optional[pd.DataFrame]:
    """
    Cache metadata.parquet per year.
    TTL: 1 hour - metadata doesn't change frequently.
    Using st.cache_data because DataFrame is serializable and changes per year.
    """
    return aws_utils.fetch_metadata_parquet(year)

@st.cache_data(ttl=7200)
def get_index_json_for_year(year: int, language: str = "english") -> Optional[Dict]:
    """
    Cache index.json files per (year, language).
    TTL: 2 hours - index files are stable.
    Using st.cache_data because dict is serializable.
    """
    return aws_utils.fetch_index_json(year, language)

@st.cache_data(ttl=3600)
def get_case_details_cached(year: int, case_id: str) -> Optional[Dict]:
    """
    Cache resolved case details per (year, case_id).
    TTL: 1 hour - case details don't change.
    Using st.cache_data because dict is serializable.
    """
    return aws_utils.get_case_metadata(year, case_id)

@st.cache_resource
def get_all_years_metadata() -> Dict[int, pd.DataFrame]:
    """
    Cache all years metadata in memory.
    Using st.cache_resource because we want to keep DataFrames in memory.
    Only loads when explicitly called - not on app startup.
    Cache invalidation: Manual clear or app restart.
    """
    import concurrent.futures
    
    years = list(range(1950, 2026))
    result = {}
    
    # Use max_workers=10 to parallelize S3 fetches
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        future_to_year = {executor.submit(get_metadata_for_year, year): year for year in years}
        for future in concurrent.futures.as_completed(future_to_year):
            year = future_to_year[future]
            try:
                df = future.result()
                if df is not None:
                    result[year] = df
            except Exception as e:
                print(f"Error fetching data for year {year}: {e}")
                
    return result

@st.cache_resource(show_spinner="Processing and normalizing all data...")
def get_processed_full_dataset() -> Optional[pd.DataFrame]:
    """
    Load ALL years, combine, and normalize.
    This is expensive, so we cache the result globally.
    """
    import os
    
    # Fast path: Load strictly from local preprocessed parquet if available
    # This aligns with the "load once" philosophy and uses the exact file structure the user verified in temp.py
    if os.path.exists("data/base_for_dashboard.parquet"):
        try:
            print("Loading from local base_for_dashboard.parquet...")
            return pd.read_parquet("data/base_for_dashboard.parquet")
        except Exception as e:
            print(f"Failed to load local parquet: {e}")
            # Fallback to S3 logic below
            
    all_data = get_all_years_metadata()
    if not all_data:
        return None
        
    dfs = []
    # Process all years
    for year, df in all_data.items():
        df = df.copy()
        df['year'] = year
        
        # Apply normalization - this is the expensive part we only want to do once
        if 'judge' in df.columns:
            df['judge'] = df['judge'].apply(preprocessing.normalize_judges)
        if 'citation' in df.columns:
            df['citation'] = df['citation'].apply(preprocessing.normalize_citations)
        if 'title' in df.columns:
            df[['petitioner', 'respondent']] = df['title'].apply(
                lambda x: pd.Series(preprocessing.extract_petitioner_respondent(x))
            )
        dfs.append(df)
        
    if not dfs:
        return None
        
    return pd.concat(dfs, ignore_index=True)

def get_combined_metadata(years: Optional[List[int]] = None) -> Optional[pd.DataFrame]:
    """
    Get combined metadata.
    Uses cached processed dataset to avoid repeated work.
    If 'years' is provided, filters the cached dataset.
    """
    # Always load the full cached dataset
    full_df = get_processed_full_dataset()
    
    if full_df is None:
        return None
        
    if years is None:
        return full_df
        
    # Filter memory-efficiently
    return full_df[full_df['year'].isin(years)]
