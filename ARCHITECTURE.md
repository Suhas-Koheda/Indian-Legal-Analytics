# Architecture & Caching Strategy

## Overview

This application fetches data directly from AWS S3 public bucket `indian-supreme-court-judgments` and implements a comprehensive caching strategy to optimize performance.

## Data Source

All data comes from AWS S3:
- **Metadata**: `s3://indian-supreme-court-judgments/metadata/parquet/year=YYYY/metadata.parquet`
- **Index Files**: `s3://indian-supreme-court-judgments/metadata/tar/year=YYYY/english.index.json`
- **Judgment PDFs**: `s3://indian-supreme-court-judgments/data/tar/year=YYYY/english/`

## Caching Strategy

### `st.cache_data` (Serializable Data)

Used for:
1. **Metadata Parquet Files** (`get_metadata_for_year`)
   - TTL: 1 hour
   - Reason: Metadata doesn't change frequently, but we want fresh data periodically
   - Cached per year to avoid re-downloading

2. **Index JSON Files** (`get_index_json_for_year`)
   - TTL: 2 hours
   - Reason: Index files are very stable, can cache longer
   - Maps PDF filenames to tar file locations

3. **Case Details** (`get_case_details_cached`)
   - TTL: 1 hour
   - Reason: Case details don't change once published
   - Cached per (year, case_id) combination

4. **Combined Metadata** (`load_data` in pages)
   - TTL: 30 minutes
   - Reason: Aggregated data, refreshed more frequently for user experience
   - Only loads years that are actually requested

### `st.cache_resource` (Heavy Objects)

Used for:
1. **All Years Metadata** (`get_all_years_metadata`)
   - Only called when explicitly needed
   - Keeps DataFrames in memory
   - Cache invalidation: Manual clear or app restart

## Cache Invalidation

- **Automatic**: TTL-based expiration
- **Manual**: "Clear All Cache" button in sidebar
- **On Error**: Cache is bypassed, fresh data fetched

## Performance Optimizations

1. **Lazy Loading**: Only fetch years that are requested
2. **Per-Year Caching**: Avoid re-downloading entire dataset
3. **Direct HTTP**: Use `requests` for public S3 bucket (faster than boto3 for public access)
4. **Selective Tar Extraction**: Only download and extract the specific tar file containing the PDF
5. **Search Ranking**: Pre-compute search scores, sort efficiently

## Search Implementation

- **Normalization**: Case-insensitive, trimmed, whitespace-normalized
- **Ranking**: Exact match (100 points) > Partial match (50 points) > Contains (25 points)
- **Multi-field**: Searches across case_id, title, petitioner, respondent, citation
- **Deterministic**: Same query always returns same results in same order

## PDF Fetching Workflow

1. User provides year and case_id
2. Fetch metadata.parquet for that year (cached)
3. Find case by case_id
4. Extract `path` field (PDF filename)
5. Fetch index.json for that year/language (cached)
6. Find which tar file contains the PDF
7. Download only that tar file
8. Extract only the required PDF from tar
9. Display/download PDF

## Module Structure

- **aws_utils.py**: S3 data fetching, PDF extraction
- **cache_utils.py**: Streamlit caching wrappers
- **search.py**: Search logic with normalization and ranking
- **ui_components.py**: Reusable UI components (charts, filters, theme)
- **pages/**: Individual page modules

## HuggingFace Spaces Compatibility

- No local file dependencies (all data from S3)
- Session state properly initialized
- Error handling for missing data
- No filesystem assumptions
- Environment variable support for API keys
