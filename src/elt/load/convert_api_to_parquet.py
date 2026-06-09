from pathlib import Path
import os
import sys
import json
import datetime
import traceback
import logging
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DATA_DIR = PROJECT_ROOT / "data"
DATA_RAW_DIR = DATA_DIR / "raw"
DATA_COMPLETE_DIR = DATA_DIR / "completed"
LOGS_DIR = PROJECT_ROOT / "logs" / "elt.log"


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


def _export_to_parquet():
    latest_file = _get_latest_file_in_directory(DATA_RAW_DIR / "ohlcs", ".json")
    if not latest_file:
        logging.warning("[Load] Warning: No raw OHLC file found.")
        return None

    with open(latest_file, "r", encoding="utf-8") as f:
        ohlc_data = json.load(f)

    processed_ohlcs = []
    for record in ohlc_data:
        processed_record = {
            "ticker": record.get("T"),
            "volume": record.get("v"),
            "vwap": record.get("vw"),
            "open": record.get("o"),
            "close": record.get("c"),
            "high": record.get("h"),
            "low": record.get("l"),
            "timestamp": record.get("t"),
            "transactions": record.get("n"),
        }
        processed_ohlcs.append(processed_record)

    df = pd.DataFrame(processed_ohlcs)

    if "timestamp" in df.columns:
        df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")

    timestamp = datetime.datetime.now().strftime("%Y_%m_%d")
    output_file = os.path.join(DATA_COMPLETE_DIR, f"ohlcs_{timestamp}.parquet")
    df.to_parquet(output_file, engine="pyarrow", compression="snappy", index=False)

    logging.info(f"[Load] Converted {len(df)} OHLC records to Parquet")
    logging.info(f"[Load] Saved to: {output_file}")
    logging.info(
        f"[Load] File size: {os.path.getsize(output_file) / (1024 * 1024):.2f} MB"
    )

    return output_file


def convert_db_to_parquet():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler(LOGS_DIR, mode="a", encoding="utf-8"),
            logging.StreamHandler(sys.stdout),
        ],
    )
    try:
        ohlc_file = _export_to_parquet()
        if ohlc_file:
            logging.info(f"[Load] OHLC: {ohlc_file}")

    except Exception as e:
        logging.error(f"[Load] Error: {e}")
        traceback.print_exc()


if __name__ == "__main__":
    convert_db_to_parquet()
