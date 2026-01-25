import pandas as pd
import json
import tarfile
import io
import requests
import re
from typing import Optional, Dict, List, Tuple

BASE_URL = "https://indian-supreme-court-judgments.s3.amazonaws.com"

def fetch_metadata_parquet(year: int) -> Optional[pd.DataFrame]:
    """
    Fetch metadata.parquet for a specific year from S3.
    Uses direct HTTP download for public bucket (faster than boto3 for public access).
    """
    url = f"{BASE_URL}/metadata/parquet/year={year}/metadata.parquet"
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        return pd.read_parquet(io.BytesIO(response.content))
    except Exception as e:
        return None

def fetch_index_json(year: int, language: str = "english") -> Optional[Dict]:
    """
    Fetch index.json for a specific year and language from S3.
    Returns dict mapping PDF filenames to tar file locations.
    """
    url = f"{BASE_URL}/data/tar/year={year}/{language}/{language}.index.json"
    print(f"\n=== FETCHING INDEX JSON ===")
    print(f"URL: {url}")
    print(f"CURL Command: curl -s '{url}'")
    
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        index_data = response.json()
        
        print(f"\n=== INDEX JSON STRUCTURE ===")
        if isinstance(index_data, dict):
            print(f"Top-level keys: {list(index_data.keys())}")
            
            # Check if V2 format
            if "parts" in index_data:
                print(f"\n[V2] Format detected (has 'parts' key)")
                print(f"Total parts: {len(index_data['parts'])}")
                for i, part in enumerate(index_data['parts'][:3]):  # Show first 3 parts
                    print(f"\nPart {i+1}:")
                    print(f"  - name: {part.get('name')}")
                    print(f"  - file_count: {part.get('file_count', len(part.get('files', [])))}")
                    print(f"  - size: {part.get('size_human', 'N/A')}")
                    if 'files' in part and len(part['files']) > 0:
                        print(f"  - first 5 files: {part['files'][:5]}")
            else:
                print(f"\n[V1] Format detected (flat dict)")
                print(f"Number of tar files: {len([k for k, v in index_data.items() if isinstance(v, list)])}")
                for i, (tar_name, files) in enumerate(list(index_data.items())[:3]):
                    if isinstance(files, list):
                        print(f"\nTar {i+1}: {tar_name}")
                        print(f"  - file_count: {len(files)}")
                        print(f"  - first 5 files: {files[:5]}")
        
        return index_data
    except Exception as e:
        print(f"ERROR fetching index: {str(e)}")
        return None

def get_pdf_location(year: int, pdf_filename: str, language: str = "english") -> Optional[str]:
    """
    Find which tar file contains a specific PDF.
    Returns the tar filename (e.g., 'data.tar' or 'data-part-1.tar').
    Handles both V1 (simple dict) and V2 (nested parts) index formats.
    """
    index = fetch_index_json(year, language)
    if not index:
        return None
        
    pdf_key = pdf_filename if pdf_filename.startswith(f"{year}/") else f"{year}/{pdf_filename}"
    
    # Check for V2 format (has "parts" key)
    # Helper to check if file is in list, trying various extensions/formats
    def is_file_in_list(filename, file_list):
        if filename in file_list:
            return True
        # Try appending .pdf
        if f"{filename}.pdf" in file_list:
            return True
        # Try appending _EN.pdf (English suffix)
        if f"{filename}_EN.pdf" in file_list:
            return True
        # Try prepending year if missing
        if f"{year}/{filename}" in file_list:
            return True
        if f"{year}/{filename}.pdf" in file_list:
            return True
        if f"{year}/{filename}_EN.pdf" in file_list:
            return True
        return False

    # Check for V2 format (has "parts" key)
    if isinstance(index, dict) and "parts" in index:
        for part in index["parts"]:
            tar_name = part.get("name")
            files = part.get("files", [])
            if is_file_in_list(pdf_filename, files):
                return tar_name
    
    # Fallback to V1 format (dict of tar_name -> file_list)
    elif isinstance(index, dict):
        for tar_file, pdfs in index.items():
            if not isinstance(pdfs, list): # Skip non-list values (metadata keys)
                continue
            if is_file_in_list(pdf_filename, pdfs):
                return tar_file
    
    return None

def download_tar_file(year: int, tar_filename: str, language: str = "english") -> Optional[bytes]:
    """
    Download a specific tar file from S3.
    Returns tar file content as bytes.
    """
    url = f"{BASE_URL}/data/tar/year={year}/{language}/{tar_filename}"
    print(url)
    try:
        response = requests.get(url, timeout=120, stream=True)
        response.raise_for_status()
        return response.content
    except Exception:
        return None

def extract_pdf_from_tar(tar_content: bytes, pdf_filename: str) -> Optional[bytes]:
    """
    Extract a specific PDF from tar file content.
    Returns PDF content as bytes.
    """
    try:
        tar_file = tarfile.open(fileobj=io.BytesIO(tar_content), mode='r:*')
        
        pdf_key = pdf_filename if '/' in pdf_filename else None
        for member in tar_file.getmembers():
            if member.name.endswith(pdf_filename) or (pdf_key and pdf_key in member.name):
                pdf_file = tar_file.extractfile(member)
                if pdf_file:
                    return pdf_file.read()
        
        return None
    except Exception:
        return None

def get_case_metadata(year: int, case_id: str) -> Optional[Dict]:
    """
    Get full metadata for a specific case by year and case_id.
    Handles case IDs that may contain year information (e.g., "2025 INSC 1401").
    Returns dict with all case fields.
    """
    case_id_str = str(case_id).strip()
    
    if not case_id_str:
        return None
    
    years_to_try = [year]
    
    year_match = re.search(r'\b(19|20)\d{2}\b', case_id_str)
    if year_match:
        extracted_year = int(year_match.group())
        if 1950 <= extracted_year <= 2025 and extracted_year not in years_to_try:
            years_to_try.insert(0, extracted_year)
    
    for try_year in years_to_try:
        df = fetch_metadata_parquet(try_year)
        if df is None or 'case_id' not in df.columns:
            continue
        
        case_id_normalized = case_id_str.lower()
        matches = df[df['case_id'].astype(str).str.strip().str.lower() == case_id_normalized]
        
        if len(matches) == 0:
            case_id_normalized_no_spaces = case_id_str.replace(' ', '').lower()
            matches = df[df['case_id'].astype(str).str.replace(' ', '').str.lower() == case_id_normalized_no_spaces]
        
        if len(matches) == 0:
            matches = df[df['case_id'].astype(str).str.contains(case_id_str, case=False, na=False)]
        
        if len(matches) > 0:
            case = matches.iloc[0].to_dict()
            actual_year = try_year
            break
    else:
        return None
    
    def normalize_list_field(value):
        if pd.isna(value) or value is None:
            return []
        if isinstance(value, list):
            return [str(v).strip() for v in value if v and str(v).strip()]
        if isinstance(value, str):
            value = value.strip()
            if not value:
                return []
            if ',' in value or ';' in value:
                return [v.strip() for v in re.split(r'[,;]', value) if v.strip()]
            return [value]
        return []
    
    def get_judges(case):
        judges = case.get('judge', case.get('judges', []))
        if pd.isna(judges) or judges is None:
            return []
        if isinstance(judges, list):
            return [str(j).strip() for j in judges if j and str(j).strip()]
        if isinstance(judges, str):
            judges_str = judges.strip()
            if not judges_str:
                return []
            if ',' in judges_str or ' and ' in judges_str.lower():
                parts = re.split(r'[,;]| and ', judges_str, flags=re.IGNORECASE)
                return [p.strip() for p in parts if p.strip()]
            return [judges_str]
        return []
    
    judges_list = get_judges(case)
    
    return {
        'title': case.get('title', ''),
        'petitioner': normalize_list_field(case.get('petitioner', '')),
        'respondent': normalize_list_field(case.get('respondent', '')),
        'judges': judges_list,
        'citation': normalize_list_field(case.get('citation', [])),
        'decision_date': case.get('decision_date', ''),
        'disposal_nature': case.get('disposal_nature', ''),
        'available_languages': normalize_list_field(case.get('available_languages', [])),
        'path': case.get('path', ''),
        'case_id': case.get('case_id', ''),
        'year': actual_year,
        'court': case.get('court', ''),
        'author_judge': normalize_list_field(case.get('author_judge', '')),
        'cnr': case.get('cnr', ''),
        'description': case.get('description', '')
    }

def get_pdf_url(year: int, case_id: str, language: str = "english") -> Optional[str]:
    """
    Get the URL to the tar file containing the PDF.
    Returns the URL string, or None if not found.
    """
    case_meta = get_case_metadata(year, case_id)
    if not case_meta or not case_meta.get('path'):
        return None
    
    pdf_path = case_meta['path']
    pdf_filename = pdf_path.split('/')[-1] if '/' in pdf_path else pdf_path
    
    tar_filename = get_pdf_location(year, pdf_filename, language)
    if not tar_filename:
        return None
    
    tar_url = f"{BASE_URL}/data/tar/year={year}/{language}/{tar_filename}"
    print(f"Debug: Generated PDF Tar URL: {tar_url}")
    return tar_url

def fetch_pdf_for_case(year: int, case_id: str, language: str = "english", pdf_path: str = None) -> Optional[bytes]:
    """
    Complete workflow: Get case metadata -> Find PDF -> Download tar -> Extract PDF.
    Returns PDF content as bytes, or None if not found.
    
    Args:
        year: Year of the case
        case_id: Case ID
        language: Language (english/regional)
        pdf_path: Optional. If provided, uses this path directly instead of fetching metadata from AWS
    """
    print(f"\n--- Starting PDF Fetch for Case ID: {case_id} (Year: {year}, Lang: {language}) ---")
    
    # If pdf_path is provided, use it directly (from local metadata)
    if pdf_path:
        print(f"Debug: Using provided PDF path: {pdf_path}")
        pdf_filename = pdf_path.split('/')[-1] if '/' in pdf_path else pdf_path
    else:
        # Fallback: fetch metadata from AWS
        case_meta = get_case_metadata(year, case_id)
        if not case_meta or not case_meta.get('path'):
            print(f"Debug: Case metadata not found or no path for year={year}, case_id={case_id}")
            return None
        
        pdf_path = case_meta['path']
        pdf_filename = pdf_path.split('/')[-1] if '/' in pdf_path else pdf_path
    print(f"Debug: Extracted PDF filename: {pdf_filename} from path: {pdf_path}")
    
    tar_filename = get_pdf_location(year, pdf_filename, language)
    if not tar_filename:
        print(f"\nERROR: TAR filename NOT FOUND in index")
        print(f"Search criteria:")
        print(f"  - year: {year}")
        print(f"  - language: {language}")
        print(f"  - pdf_filename: {pdf_filename}")
        print(f"\nRe-fetching index for detailed inspection...")
        index = fetch_index_json(year, language)
        
        if index:
            if isinstance(index, dict) and "parts" in index:
                print(f"\nSearching through {len(index['parts'])} parts for matching file...")
                for i, part in enumerate(index['parts']):
                    files = part.get('files', [])
                    print(f"\nPart {i+1} ({part.get('name')}): {len(files)} files")
                    # Check if any filename is similar
                    similar = [f for f in files if pdf_filename[:10] in f]
                    if similar:
                        print(f"  - Similar filenames found: {similar[:10]}")
            else:
                print(f"\nV1 format - tar file keys: {list(index.keys())[:10]}")
        return None
    
    print(f"Debug: TAR filename found: {tar_filename}")
    
    tar_url = f"{BASE_URL}/data/tar/year={year}/{language}/{tar_filename}"
    print(f"Debug: Downloading TAR from: {tar_url}")
    
    tar_content = download_tar_file(year, tar_filename, language)
    if not tar_content:
        print(f"Debug: Failed to download TAR file: {tar_filename}")
        return None
    
    print(f"Debug: TAR downloaded, size: {len(tar_content)} bytes. Extracting {pdf_filename}...")
    
    # Custom extraction with logging of contents if fail
    try:
        tar_file = tarfile.open(fileobj=io.BytesIO(tar_content), mode='r:*')
        members = tar_file.getmembers()
        print(f"Debug: TAR contains {len(members)} files.")
        
        pdf_key = pdf_filename if '/' in pdf_filename else None
        
        for member in members:
            # Check for exact match or suffix match or key match or .pdf extension match
            # Also check for language suffixes like _EN.pdf
            if (member.name.endswith(pdf_filename) or 
                (pdf_key and pdf_key in member.name) or
                member.name.endswith(f"{pdf_filename}.pdf") or
                member.name.endswith(f"{pdf_filename}_EN.pdf") or
                (pdf_key and f"{pdf_key}.pdf" in member.name) or
                (pdf_key and f"{pdf_key}_EN.pdf" in member.name)):
                
                print(f"Debug: Found matching file in TAR: {member.name}")
                pdf_file = tar_file.extractfile(member)
                if pdf_file:
                    content = pdf_file.read()
                    print(f"Debug: Successfully extracted PDF, size: {len(content)} bytes")
                    return content
        
        print(f"Debug: PDF {pdf_filename} NOT found in TAR.")
        print(f"Debug: First 10 files in TAR for debugging:")
        for m in members[:10]:
            print(f" - {m.name}")
            
    except Exception as e:
        print(f"Debug: Exception during tar extraction: {str(e)}")
        import traceback
        traceback.print_exc()
    
    return None
