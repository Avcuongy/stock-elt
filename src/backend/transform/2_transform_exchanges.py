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


def transform_exchanges():
    """
    Transform raw markets data and extract exchanges to processed/exchanges folder.
    """
    # Define paths
    base_dir = os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    )
    raw_dir = os.path.join(base_dir, "data", "raw", "markets")
    processed_dir = os.path.join(base_dir, "data", "processed", "exchanges")

    # Ensure processed directory exists
    os.makedirs(processed_dir, exist_ok=True)

    # Get latest raw markets file
    latest_file = get_latest_file_in_directory(raw_dir, ".json")
    if not latest_file:
        print("No raw markets file found.")
        return

    print(f"Processing file: {latest_file}")

    # Load raw data
    with open(latest_file, "r", encoding="utf-8") as f:
        raw_data = json.load(f)

    # Extract exchanges
    exchanges_dict = {}

    for item in raw_data:
        region = item.get("region", "")
        market_type = item.get("market_type", "")
        primary_exchanges = item.get("primary_exchanges", "")
        local_open = item.get("local_open", "")
        local_close = item.get("local_close", "")

        # Split comma-separated exchanges
        exchange_list = [
            ex.strip() for ex in primary_exchanges.split(",") if ex.strip()
        ]

        for exchange_name in exchange_list:
            # Create unique key
            key = exchange_name

            if key not in exchanges_dict:
                exchanges_dict[key] = {
                    "id": generate_id(exchange_name),
                    "name": exchange_name,
                    "region": region,
                    "market_type": market_type,
                    "local_open": local_open,
                    "local_close": local_close,
                }

    # Convert to list
    exchanges = list(exchanges_dict.values())

    # Generate output filename with timestamp
    today = datetime.datetime.now().strftime("%Y_%m_%d")
    output_file = os.path.join(processed_dir, f"process_exchanges_{today}.json")

    # Save processed data
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(exchanges, f, indent=2, ensure_ascii=False)

    print(f"Processed {len(exchanges)} exchanges.")
    print(f"Saved to: {output_file}")

    return exchanges


if __name__ == "__main__":
    transform_exchanges()
