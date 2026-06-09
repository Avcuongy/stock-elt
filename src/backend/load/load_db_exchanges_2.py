from pathlib import Path
import os
import json
import logging
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.exc import IntegrityError
from utils.config_env import DATABASE_URL

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DATA_DIR = PROJECT_ROOT / "data"
DATA_PROCESSED_DIR = DATA_DIR / "processed"
LOGS_DIR = DATA_DIR / "logs" / "backend.log"


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


def _get_db_connection():
    database_url = DATABASE_URL
    if not database_url:
        raise ValueError("DATABASE_URL not found")

    engine = create_engine(database_url, echo=False)
    return engine


def _load_exchanges(engine):
    latest_file = _get_latest_file_in_directory(DATA_PROCESSED_DIR, ".json")
    if not latest_file:
        logging.info("[Backend - Load] No processed exchanges file found.")
        return

    logging.info(f"[Backend - Load] Loading exchanges from: {latest_file}")

    with open(latest_file, "r", encoding="utf-8") as f:
        exchanges_data = json.load(f)

    inserted = 0
    skipped = 0
    errors = 0

    with engine.connect() as conn:
        for exchange in exchanges_data:
            try:
                exchange_name = exchange.get("name")
                region_name = exchange.get("region")

                if not exchange_name:
                    logging.info(
                        f"[Backend - Load] Skipping exchange with no name: {exchange}"
                    )
                    skipped += 1
                    continue

                region_query = text("""
                    SELECT region_id FROM regions WHERE region_name = :region_name
                """)
                result = conn.execute(region_query, {"region_name": region_name})
                region_row = result.fetchone()

                if not region_row:
                    logging.info(
                        f"[Backend - Load] Warning: Region '{region_name}' not found for exchange '{exchange_name}'. Skipping."
                    )
                    errors += 1
                    continue

                region_id = region_row[0]

                sql = text("""
                    INSERT INTO exchanges (exchange_name, exchange_region_id)
                    VALUES (:name, :region_id)
                    ON DUPLICATE KEY UPDATE
                        exchange_region_id = :region_id
                """)

                conn.execute(sql, {"name": exchange_name, "region_id": region_id})
                conn.commit()
                inserted += 1

            except IntegrityError as e:
                skipped += 1
                logging.info(
                    f"[Backend - Load] Skipped exchange {exchange.get('name')}: {e}"
                )
            except Exception as e:
                errors += 1
                logging.error(
                    f"[Backend - Load] Error inserting exchange {exchange.get('name')}: {e}"
                )

    logging.info(
        f"[Backend - Load] Exchanges: {inserted} inserted/updated, {skipped} skipped, {errors} errors"
    )


def load_db_exchanges():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler(LOGS_DIR, mode="a", encoding="utf-8"),
            logging.StreamHandler(sys.stdout),
        ],
    )
    logging.info("[Backend - Load] Loading Exchanges to MySQL")
    try:
        engine = _get_db_connection()
        _load_exchanges(engine)
    except Exception as e:
        logging.error(f"[Backend - Load] Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    load_db_exchanges()
