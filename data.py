import os
import requests
from tqdm import tqdm

BASE_URL = "https://indian-supreme-court-judgments.s3.amazonaws.com"
START_YEAR = 1950
END_YEAR = 2025
OUTPUT_DIR = "parquet_metadata"

os.makedirs(OUTPUT_DIR, exist_ok=True)

for year in tqdm(range(START_YEAR, END_YEAR + 1), desc="Downloading years"):
    url = f"{BASE_URL}/metadata/parquet/year={year}/metadata.parquet"
    local_path = os.path.join(OUTPUT_DIR, f"metadata_{year}.parquet")

    try:
        head = requests.head(url, timeout=10)
        if head.status_code != 200:
            print(f"Skipping {year} (not available)")
            continue

        with requests.get(url, stream=True, timeout=60) as r:
            r.raise_for_status()
            with open(local_path, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)

        print(f"Downloaded {year}")

    except Exception as e:
        print(f"Failed {year}: {e}")

print("\nDownload complete!")
print(f"Files saved in: {OUTPUT_DIR}/")
