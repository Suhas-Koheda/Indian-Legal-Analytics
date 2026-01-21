import pandas as pd

PARQUET_FILES = {
    "BASE DATASET": "data/base_for_dashboard.parquet",
    "YEARLY CASES BY JUDGE": "data/yearly_cases_by_judge.parquet",
    "YEARLY CASES BY LEGAL PROVISION": "data/yearly_cases_by_provision.parquet",
}


def inspect_parquet(name, path):
    print("\n" + "=" * 70)
    print(f"{name}")
    print("=" * 70)

    try:
        df = pd.read_parquet(path)
    except FileNotFoundError:
        print(f"File not found: {path}")
        return

    print("Shape:", df.shape)

    print("\nColumns:")
    for col in df.columns:
        print(f" - {col}")

    if "year" in df.columns:
        print("\nYear range:", df["year"].min(), "-", df["year"].max())

    print("\n--- Head (3 rows) ---")
    print(df.head(3))


if __name__ == "__main__":
    for name, path in PARQUET_FILES.items():
        inspect_parquet(name, path)
