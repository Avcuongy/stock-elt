from pathlib import Path
import os
import sys
import json
import datetime
import logging
import hashlib

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DATA_DIR = PROJECT_ROOT / "data"
DATA_RAW_DIR = DATA_DIR / "raw"
DATA_PROCESSED_DIR = DATA_DIR / "processed"
LOGS_DIR = PROJECT_ROOT / "logs" / "backend.log"


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


def _generate_id(text):
    return hashlib.md5(text.encode()).hexdigest()


def _transform_sic_industries(companies_data):
    sic_industries_dict = {}

    for item in companies_data:
        sic = item.get("sic", "")
        sic_sector = item.get("sicSector", "")
        sic_industry = item.get("sicIndustry", "")

        if sic and sic not in sic_industries_dict:
            sic_industries_dict[sic] = {
                "id": _generate_id(sic),
                "sic": sic,
                "sicSector": sic_sector,
                "sicIndustry": sic_industry,
            }

    return list(sic_industries_dict.values())


def _transform_industries(companies_data):
    industries_dict = {}

    for item in companies_data:
        sector = item.get("sector", "")
        industry = item.get("industry", "")

        if industry and industry not in industries_dict:
            key = industry
            industries_dict[key] = {
                "id": _generate_id(industry),
                "sector": sector,
                "industry": industry,
            }

    return list(industries_dict.values())


def _transform_regions(markets_data):
    regions_dict = {}

    for item in markets_data:
        region = item.get("region", "")
        market_type = item.get("market_type", "")

        if region and region not in regions_dict:
            regions_dict[region] = {
                "id": _generate_id(region),
                "region": region,
                "market_type": market_type,
            }

    return list(regions_dict.values())


def transform_others():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler(LOGS_DIR, mode="a", encoding="utf-8"),
            logging.StreamHandler(sys.stdout),
        ],
    )
    companies_raw_dir = DATA_RAW_DIR / "companies"
    markets_raw_dir = DATA_RAW_DIR / "markets"

    sicindustries_processed_dir = DATA_PROCESSED_DIR / "sicindustries"
    industries_processed_dir = DATA_PROCESSED_DIR / "industries"
    regions_processed_dir = DATA_PROCESSED_DIR / "regions"

    companies_file = _get_latest_file_in_directory(companies_raw_dir, ".json")
    markets_file = _get_latest_file_in_directory(markets_raw_dir, ".json")

    if not companies_file:
        logging.info("[Backend - Transform] No raw companies file found.")
        return

    if not markets_file:
        logging.info("[Backend - Transform] No raw markets file found.")
        return

    with open(companies_file, "r", encoding="utf-8") as f:
        companies_data = json.load(f)

    with open(markets_file, "r", encoding="utf-8") as f:
        markets_data = json.load(f)

    today = datetime.datetime.now().strftime("%Y_%m_%d")

    # SIC Industries
    sic_industries = _transform_sic_industries(companies_data)
    sic_output_file = sicindustries_processed_dir / f"sicindustries_{today}.json"
    with open(sic_output_file, "w", encoding="utf-8") as f:
        json.dump(sic_industries, f, indent=2, ensure_ascii=False)
    logging.info(
        f"[Backend - Transform] Transformed {len(sic_industries)} SIC industries."
    )

    # Industries
    industries = _transform_industries(companies_data)
    industries_output_file = industries_processed_dir / f"industries_{today}.json"
    with open(industries_output_file, "w", encoding="utf-8") as f:
        json.dump(industries, f, indent=2, ensure_ascii=False)
    logging.info(f"[Backend - Transform] Transformed {len(industries)} industries.")

    # Regions
    regions = _transform_regions(markets_data)
    regions_output_file = regions_processed_dir / f"regions_{today}.json"
    with open(regions_output_file, "w", encoding="utf-8") as f:
        json.dump(regions, f, indent=2, ensure_ascii=False)
    logging.info(f"[Backend - Transform] Transformed {len(regions)} regions.")

    return {
        "sic_industries": sic_industries,
        "industries": industries,
        "regions": regions,
    }


if __name__ == "__main__":
    transform_others()
