import os
import json
import datetime

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


def transform_companies():
    """
    Transform raw companies data and save to processed/companies folder.
    """
    # Define paths
    base_dir = os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    )
    raw_dir = os.path.join(base_dir, "data", "raw", "companies")
    processed_dir = os.path.join(base_dir, "data", "processed", "companies")

    # Ensure processed directory exists
    os.makedirs(processed_dir, exist_ok=True)

    # Get latest raw companies file
    latest_file = get_latest_file_in_directory(raw_dir, ".json")
    if not latest_file:
        print("No raw companies file found.")
        return

    print(f"Processing file: {latest_file}")

    # Load raw data
    with open(latest_file, "r", encoding="utf-8") as f:
        raw_data = json.load(f)

    # Transform companies data
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

    # Generate output filename with timestamp
    today = datetime.datetime.now().strftime("%Y_%m_%d")
    output_file = os.path.join(processed_dir, f"process_companies_{today}.json")

    # Save processed data
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(companies, f, indent=2, ensure_ascii=False)

    print(f"Processed {len(companies)} companies.")
    print(f"Saved to: {output_file}")

    return companies


if __name__ == "__main__":
    transform_companies()
