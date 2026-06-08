from pathlib import Path
import os
import json
import datetime

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DATA_DIR = PROJECT_ROOT / "data"
DATA_RAW_DIR = DATA_DIR / "raw"
DATA_PROCESSED_DIR = DATA_DIR / "processed"


def _get_latest_file_in_directory(directory, extension):
    files = [
        os.path.join(directory, f)
        for f in os.listdir(directory)
        if f.endswith(extension)
    ]
    if not files:
        return None
    latest_file = max(files, key=os.path.getmtime)
    return latest_file


def transform_companies():

    latest_file = _get_latest_file_in_directory(DATA_RAW_DIR / "companies", ".json")
    if not latest_file:
        print("[Backend - Transform] No raw companies file found.")
        return

    with open(latest_file, "r", encoding="utf-8") as f:
        raw_data = json.load(f)

    companies = []
    for item in raw_data:
        company = {
            "id": item.get("id"),
            "name": item.get("name"),
            "ticker": item.get("ticker"),
            "cik": item.get("cik"),
            "cusip": item.get("cusip"),
            "exchange": item.get("exchange"),
            "isDelisted": item.get("isDelisted"),
            "category": item.get("category"),
            "sector": item.get("sector"),
            "industry": item.get("industry"),
            "sic": item.get("sic"),
            "currency": item.get("currency"),
            "location": item.get("location"),
        }
        companies.append(company)

    today = datetime.datetime.now().strftime("%Y_%m_%d")
    output_file = DATA_PROCESSED_DIR / "companies" / f"companies_{today}.json"

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(companies, f, indent=2, ensure_ascii=False)

    print(f"[Backend - Transform] Transformed {len(companies)} companies.")

    return companies


if __name__ == "__main__":
    transform_companies()
