import pandas as pd
from typing import List, Dict, Tuple
import re

def normalize_text(text: str) -> str:
    """Normalize text for search: lowercase, trim, remove extra spaces"""
    if pd.isna(text) or text is None:
        return ""
    return re.sub(r'\s+', ' ', str(text).strip().lower())

def search_cases(
    df: pd.DataFrame,
    query: str,
    search_fields: List[str] = ['case_id', 'title', 'petitioner', 'respondent', 'citation', 'judge']
) -> pd.DataFrame:
    """
    Search cases with normalization and ranking.
    Returns ranked results: exact matches first, then partial matches.
    """
    if not query or not query.strip():
        return df
    
    if len(df) == 0:
        return pd.DataFrame()
    
    query_normalized = normalize_text(query)
    if not query_normalized:
        return df
    
    df = df.reset_index(drop=True)
    results = []
    
    for idx, row in df.iterrows():
        score = 0
        match_type = None
        
        for field in search_fields:
            if field not in df.columns:
                continue
            
            field_value = row[field]
            
            # Handle None, NaN, and empty lists safely
            if field_value is None:
                continue
            if isinstance(field_value, float) and pd.isna(field_value):
                continue
            if isinstance(field_value, list) and len(field_value) == 0:
                continue
            
            if field in ['petitioner', 'respondent', 'judge', 'citation']:
                if isinstance(field_value, list):
                    field_text = ' '.join(str(v) for v in field_value)
                else:
                    field_text = str(field_value)
            else:
                field_text = str(field_value)
            
            field_normalized = normalize_text(field_text)
            
            if query_normalized == field_normalized:
                score += 100
                match_type = 'exact'
            elif query_normalized in field_normalized:
                score += 50
                if match_type != 'exact':
                    match_type = 'partial'
            elif field_normalized in query_normalized:
                score += 25
                if match_type not in ['exact', 'partial']:
                    match_type = 'contains'
        
        if score > 0:
            results.append((idx, score, match_type))
    
    if not results:
        return pd.DataFrame()
    
    results.sort(key=lambda x: (-x[1], x[0]))
    
    matched_indices = [idx for idx, _, _ in results]
    scores = [score for _, score, _ in results]
    match_types = [match_type for _, _, match_type in results]
    
    result_df = df.iloc[matched_indices].copy()
    result_df['_search_score'] = scores
    result_df['_match_type'] = match_types
    
    return result_df

def search_by_case_id(df: pd.DataFrame, case_id: str) -> pd.DataFrame:
    """Search for exact case_id match"""
    case_id_normalized = normalize_text(str(case_id))
    if 'case_id' not in df.columns:
        return pd.DataFrame()
    
    matches = df[df['case_id'].astype(str).apply(normalize_text) == case_id_normalized]
    return matches

def search_by_petitioner(df: pd.DataFrame, petitioner: str) -> pd.DataFrame:
    """Search by petitioner name"""
    petitioner_normalized = normalize_text(petitioner)
    if 'petitioner' not in df.columns:
        return pd.DataFrame()
    
    def matches_petitioner(row):
        petitioners = row.get('petitioner', [])
        if isinstance(petitioners, list):
            return any(petitioner_normalized in normalize_text(str(p)) for p in petitioners)
        return petitioner_normalized in normalize_text(str(petitioners))
    
    return df[df.apply(matches_petitioner, axis=1)]

def search_by_respondent(df: pd.DataFrame, respondent: str) -> pd.DataFrame:
    """Search by respondent name"""
    respondent_normalized = normalize_text(respondent)
    if 'respondent' not in df.columns:
        return pd.DataFrame()
    
    def matches_respondent(row):
        respondents = row.get('respondent', [])
        if isinstance(respondents, list):
            return any(respondent_normalized in normalize_text(str(r)) for r in respondents)
        return respondent_normalized in normalize_text(str(respondents))
    
    return df[df.apply(matches_respondent, axis=1)]

def search_by_citation(df: pd.DataFrame, citation: str) -> pd.DataFrame:
    """Search by citation"""
    citation_normalized = normalize_text(citation)
    if 'citation' not in df.columns:
        return pd.DataFrame()
    
    def matches_citation(row):
        citations = row.get('citation', [])
        if isinstance(citations, list):
            return any(citation_normalized in normalize_text(str(c)) for c in citations)
        return citation_normalized in normalize_text(str(citations))
    
    return df[df.apply(matches_citation, axis=1)]
