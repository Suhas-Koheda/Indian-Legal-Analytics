import os
import re
import pandas as pd

PARQUET_DIR = "parquet_metadata"
BASE_OUTPUT = "data/base_for_dashboard.parquet"
JUDGE_YEAR_OUTPUT = "data/yearly_cases_by_judge.parquet"
CITATION_YEAR_OUTPUT = "data/yearly_cases_by_citation.parquet"

def extract_year(filename):
    match = re.search(r"(\d{4})", filename)
    return int(match.group(1)) if match else None

def normalize_judges(judge_value):
    if pd.isna(judge_value):
        return []

    if isinstance(judge_value, list):
        return judge_value

    parts = re.split(r",| and ", str(judge_value))
    return [p.strip() for p in parts if p.strip()]

def normalize_citations(citation_value):
    if pd.isna(citation_value):
        return []

    if isinstance(citation_value, list):
        return citation_value

    parts = re.split(r",|;", str(citation_value))
    return [p.strip() for p in parts if len(p.strip()) > 3]
def combine_parquets():
    dfs = []

    for fname in sorted(os.listdir(PARQUET_DIR)):
        if not fname.endswith(".parquet"):
            continue

        year = extract_year(fname)
        path = os.path.join(PARQUET_DIR, fname)

        print(f"Processing {fname} | year={year}")

        df = pd.read_parquet(path)

        df["year"] = year

        if "judge" in df.columns:
            df["judge"] = df["judge"].apply(normalize_judges)
        else:
            df["judge"] = [[]] * len(df)

        if "citation" in df.columns:
            df["citation"] = df["citation"].apply(normalize_citations)
        else:
            df["citation"] = [[]] * len(df)

        dfs.append(df)

    return pd.concat(dfs, ignore_index=True)

def build_judge_year_analytics(df):
    judge_year = (
        df.explode("judge")
        .dropna(subset=["judge"])
        .groupby(["judge", "year"])
        .size()
        .reset_index(name="case_count")
    )

    return judge_year

def build_citation_year_analytics(df):
    citation_year = (
        df.explode("citation")
        .dropna(subset=["citation"])
        .groupby(["citation", "year"])
        .size()
        .reset_index(name="case_count")
    )

    return citation_year

def run():
    os.makedirs("data", exist_ok=True)

    combined_df = combine_parquets()

    judge_year_df = build_judge_year_analytics(combined_df)
    citation_year_df = build_citation_year_analytics(combined_df)

    combined_df.to_parquet(BASE_OUTPUT, index=False)
    judge_year_df.to_parquet(JUDGE_YEAR_OUTPUT, index=False)
    citation_year_df.to_parquet(CITATION_YEAR_OUTPUT, index=False)

    print("Preprocessing completed (STRICT MODE)")
    print(f"- {BASE_OUTPUT}")
    print(f"- {JUDGE_YEAR_OUTPUT}")
    print(f"- {CITATION_YEAR_OUTPUT}")


if __name__ == "__main__":
    run()
