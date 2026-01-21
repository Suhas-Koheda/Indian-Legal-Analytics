import os
import re
import pandas as pd
from utils import clean_html

PARQUET_DIR = "parquet_metadata"
COMBINED_FILE = "data/combined_cleaned.parquet"
ANALYTICS_OUTPUT = "data/base_for_dashboard.parquet"

def extract_year(filename):
    match = re.search(r"(\d{4})", filename)
    return int(match.group(1)) if match else None

def combine_parquets():
    all_dfs = []

    for fname in sorted(os.listdir(PARQUET_DIR)):
        if not fname.endswith(".parquet"):
            continue

        path = os.path.join(PARQUET_DIR, fname)
        year = extract_year(fname)

        print(f"Processing {fname} | year={year}")

        df = pd.read_parquet(path)
        df["year"] = year
        df["clean_text"] = df["raw_html"].apply(clean_html)

        all_dfs.append(df)

    combined_df = pd.concat(all_dfs, ignore_index=True)
    return combined_df

def normalize_judges(judges):
    if pd.isna(judges):
        return []

    if isinstance(judges, list):
        return [j.strip() for j in judges if j.strip()]

    judges = re.split(r",|;| and ", str(judges))
    return [j.strip() for j in judges if j.strip()]

def extract_articles_from_text(text):
    if pd.isna(text):
        return []

    pattern = r"(?:Article|Articles|Art\.?)\s+\d+[A-Za-z]?(?:\([\w\d]+\))*"
    matches = re.findall(pattern, text, flags=re.IGNORECASE)

    articles = set()
    for m in matches:
        num = re.findall(r"\d+[A-Za-z]?(?:\([\w\d]+\))*", m)
        if num:
            articles.add(f"Article {num[0]}")

    return sorted(list(articles))

def preprocess_for_analytics(df):
    required = {"year", "clean_text"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    if "judges" in df.columns:
        df["judge_list"] = df["judges"].apply(normalize_judges)
    else:
        df["judge_list"] = [[]] * len(df)

    judges_df = df.explode("judge_list")
    judges_df = judges_df[judges_df["judge_list"].notna() & (judges_df["judge_list"] != "")]
    judges_df["judge_list"] = judges_df["judge_list"].str.title()

    if "articles" in df.columns:
        df["article_list"] = df["articles"].apply(
            lambda x: x if isinstance(x, list) else []
        )
    else:
        df["article_list"] = df["clean_text"].apply(extract_articles_from_text)

    articles_df = df.explode("article_list")
    articles_df = articles_df[
        articles_df["article_list"].notna() & (articles_df["article_list"] != "")
    ]

    cases_per_judge = (
        judges_df.groupby(["judge_list", "year"])
        .size()
        .reset_index(name="case_count")
    )

    total_cases_per_judge = (
        judges_df.groupby("judge_list")
        .size()
        .reset_index(name="total_cases")
        .sort_values("total_cases", ascending=False)
    )

    cases_per_article = (
        articles_df.groupby(["article_list", "year"])
        .size()
        .reset_index(name="case_count")
    )

    total_cases_per_article = (
        articles_df.groupby("article_list")
        .size()
        .reset_index(name="total_cases")
        .sort_values("total_cases", ascending=False)
    )

    return df, cases_per_judge, total_cases_per_judge, cases_per_article, total_cases_per_article

def save_datasets(base_df, cases_per_judge, total_cases_per_judge, cases_per_article, total_cases_per_article):
    os.makedirs("data", exist_ok=True)

    base_df.to_parquet(ANALYTICS_OUTPUT, index=False)
    cases_per_judge.to_parquet("data/cases_per_judge.parquet", index=False)
    total_cases_per_judge.to_parquet("data/total_cases_per_judge.parquet", index=False)
    cases_per_article.to_parquet("data/cases_per_article.parquet", index=False)
    total_cases_per_article.to_parquet("data/total_cases_per_article.parquet", index=False)

    print("Saved analytics-ready datasets:")
    print("- base_for_dashboard.parquet")
    print("- cases_per_judge.parquet")
    print("- total_cases_per_judge.parquet")
    print("- cases_per_article.parquet")
    print("- total_cases_per_article.parquet")

def run_preprocessing():
    print("Starting data preprocessing pipeline...")

    print("Step 1: Combining parquet files...")
    combined_df = combine_parquets()
    combined_df.to_parquet(COMBINED_FILE, index=False)
    print(f"Combined data saved to {COMBINED_FILE}")
    print(f"Shape: {combined_df.shape}")

    print("Step 2: Processing for analytics...")
    base_df, cases_per_judge, total_cases_per_judge, cases_per_article, total_cases_per_article = preprocess_for_analytics(combined_df)

    print("Step 3: Saving datasets...")
    save_datasets(base_df, cases_per_judge, total_cases_per_judge, cases_per_article, total_cases_per_article)

    print("Preprocessing pipeline completed successfully!")

if __name__ == "__main__":
    run_preprocessing()