import datetime
import json
import logging
import os
import sys
from pathlib import Path

from sqlalchemy import create_engine, text
from sqlalchemy.exc import IntegrityError
from utils.config_env import DATABASE_URL
from utils.logger import get_logger

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DATA_DIR = PROJECT_ROOT / "data"
DATA_PROCESSED_DIR = DATA_DIR / "processed"

logger = get_logger(__name__, "backend")


def _get_latest_file_in_directory(directory, extension):
    if not os.path.exists(directory):
        return None
    files = [
        os.path.join(directory, f)
        for f in os.listdir(directory)
        if f.endswith(extension) and not f.startswith(".")
    ]
    if not files:
        return None
    latest_file = max(files, key=os.path.getmtime)
    return latest_file


def _get_db_connection():
    database_url = DATABASE_URL
    if not database_url:
        raise ValueError("DATABASE_URL not found")

    engine = create_engine(database_url, echo=False, pool_pre_ping=True)
    return engine


def _load_exchanges(engine):
    latest_file = _get_latest_file_in_directory(
        DATA_PROCESSED_DIR / "exchanges", ".json"
    )
    if not latest_file:
        logger.info("[Backend - Load] No processed exchanges file found.")
        return

    logger.info(f"[Backend - Load] Loading exchanges from: {latest_file}")

    with open(latest_file, "r", encoding="utf-8") as f:
        exchanges_data = json.load(f)

    inserted = 0
    skipped = 0
    errors = 0

    insert_sql = text("""
        INSERT INTO exchanges (exchange_name, exchange_region_id)
        VALUES (:name, :region_id)
        ON DUPLICATE KEY UPDATE
            exchange_region_id = :region_id
    """)

    with engine.begin() as conn:
        region_map = {}
        region_query = text("SELECT region_name, region_id FROM regions")
        result = conn.execute(region_query)
        for row in result.fetchall():
            region_map[row[0]] = row[1]

        for exchange in exchanges_data:
            try:
                exchange_name = exchange.get("name")
                region_name = exchange.get("region")

                if not exchange_name:
                    logger.warning(
                        f"[Backend - Load] Skipping exchange with no name: {exchange}"
                    )
                    skipped += 1
                    continue

                region_id = region_map.get(region_name)

                if not region_id:
                    logger.warning(
                        f"[Backend - Load] Warning: Region '{region_name}' not found in DB for exchange '{exchange_name}'. Skipping."
                    )
                    errors += 1
                    continue

                conn.execute(
                    insert_sql, {"name": exchange_name, "region_id": region_id}
                )
                inserted += 1

            except IntegrityError as e:
                skipped += 1
                logger.warning(
                    f"[Backend - Load] Skipped exchange {exchange.get('name')} (IntegrityError): {e}"
                )
            except Exception as e:
                errors += 1
                logger.error(
                    f"[Backend - Load] Error inserting exchange {exchange.get('name')}: {e}"
                )

    logger.info(
        f"[Backend - Load] Exchanges: {inserted} inserted/updated, {skipped} skipped, {errors} errors"
    )


def load_db_exchanges():
    logger.info("[Backend - Load] Loading Exchanges to database")
    try:
        engine = _get_db_connection()
        _load_exchanges(engine)
    except Exception as e:
        logger.error(f"[Backend - Load] Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    load_db_exchanges()
