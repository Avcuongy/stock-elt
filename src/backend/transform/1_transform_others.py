import os
import json
import datetime
import hashlib

import numpy as np
import pandas as pd

from sqlalchemy import create_engine


def get_latest_file_in_directory(directory, extension):
    """
    Get the latest file in a directory with a specific extension.

    :param directory: Directory to search for files.
    :param extension: File extension to look for.
    :return: Path to the latest file or None if no files are found.
    """
    files = [
        os.path.join(directory, f)
        for f in os.listdir(directory)
        if f.endswith(extension)
    ]
    if not files:
        return None
    latest_file = max(files, key=os.path.getmtime)
    return latest_file


def generate_id(text):
    """Generate a unique ID from text using MD5 hash."""
    return hashlib.md5(text.encode()).hexdigest()


def transform_sic_industries(companies_data):
    """
    Extract SIC industries from companies data.
    """
    sic_industries_dict = {}

    for item in companies_data:
        sic = item.get("sic", "")
        sic_sector = item.get("sicSector", "")
        sic_industry = item.get("sicIndustry", "")

        if sic and sic not in sic_industries_dict:
            sic_industries_dict[sic] = {
                "id": generate_id(sic),
                "sic": sic,
                "sicSector": sic_sector,
                "sicIndustry": sic_industry,
            }

    return list(sic_industries_dict.values())


def transform_industries(companies_data):
    """
    Extract industries from companies data.
    """
    industries_dict = {}

    for item in companies_data:
        sector = item.get("sector", "")
        industry = item.get("industry", "")

        if industry and industry not in industries_dict:
            key = industry
            industries_dict[key] = {
                "id": generate_id(industry),
                "sector": sector,
                "industry": industry,
            }

    return list(industries_dict.values())


def transform_regions(markets_data):
    """
    Extract regions from markets data.
    """
    regions_dict = {}

    for item in markets_data:
        region = item.get("region", "")
        market_type = item.get("market_type", "")

        if region and region not in regions_dict:
            regions_dict[region] = {
                "id": generate_id(region),
                "region": region,
                "market_type": market_type,
            }

    return list(regions_dict.values())


def transform_others():
    """
    Transform raw companies and markets data to extract:
    - SIC industries
    - Industries
    - Regions
    """
    # Define paths
    base_dir = os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    )
    companies_raw_dir = os.path.join(base_dir, "data", "raw", "companies")
    markets_raw_dir = os.path.join(base_dir, "data", "raw", "markets")

    sicindustries_processed_dir = os.path.join(
        base_dir, "data", "processed", "sicindustries"
    )
    industries_processed_dir = os.path.join(base_dir, "data", "processed", "industries")
    regions_processed_dir = os.path.join(base_dir, "data", "processed", "regions")

    # Ensure processed directories exist
    os.makedirs(sicindustries_processed_dir, exist_ok=True)
    os.makedirs(industries_processed_dir, exist_ok=True)
    os.makedirs(regions_processed_dir, exist_ok=True)

    # Get latest raw files
    companies_file = get_latest_file_in_directory(companies_raw_dir, ".json")
    markets_file = get_latest_file_in_directory(markets_raw_dir, ".json")

    if not companies_file:
        print("No raw companies file found.")
        return

    if not markets_file:
        print("No raw markets file found.")
        return

    print(f"Processing companies file: {companies_file}")
    print(f"Processing markets file: {markets_file}")

    # Load raw data
    with open(companies_file, "r", encoding="utf-8") as f:
        companies_data = json.load(f)

    with open(markets_file, "r", encoding="utf-8") as f:
        markets_data = json.load(f)

    # Transform data
    today = datetime.datetime.now().strftime("%Y_%m_%d")

    # 1. SIC Industries
    print("\nProcessing SIC Industries...")
    sic_industries = transform_sic_industries(companies_data)
    sic_output_file = os.path.join(
        sicindustries_processed_dir, f"process_sicindustries_{today}.json"
    )
    with open(sic_output_file, "w", encoding="utf-8") as f:
        json.dump(sic_industries, f, indent=2, ensure_ascii=False)
    print(f"Processed {len(sic_industries)} SIC industries.")
    print(f"Saved to: {sic_output_file}")

    # 2. Industries
    print("\nProcessing Industries...")
    industries = transform_industries(companies_data)
    industries_output_file = os.path.join(
        industries_processed_dir, f"process_industries_{today}.json"
    )
    with open(industries_output_file, "w", encoding="utf-8") as f:
        json.dump(industries, f, indent=2, ensure_ascii=False)
    print(f"Processed {len(industries)} industries.")
    print(f"Saved to: {industries_output_file}")

    # 3. Regions
    print("\nProcessing Regions...")
    regions = transform_regions(markets_data)
    regions_output_file = os.path.join(
        regions_processed_dir, f"process_regions_{today}.json"
    )
    with open(regions_output_file, "w", encoding="utf-8") as f:
        json.dump(regions, f, indent=2, ensure_ascii=False)
    print(f"Processed {len(regions)} regions.")
    print(f"Saved to: {regions_output_file}")

    return {
        "sic_industries": sic_industries,
        "industries": industries,
        "regions": regions,
    }


if __name__ == "__main__":
    transform_others()
