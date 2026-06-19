import datetime
import logging
import os
import sys
import traceback
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine, text
from utils.config_env import DATABASE_URL
from utils.logger import get_logger

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DATA_DIR = PROJECT_ROOT / "data"
DATA_RAW_DIR = DATA_DIR / "raw"
DATA_COMPLETE_DIR = DATA_DIR / "completed"
LOGS_DIR = PROJECT_ROOT / "logs" / "elt.log"
DATABASE_URL = DATABASE_URL
TABLES = [
    "regions",
    "exchanges",
    "industries",
    "sicindustries",
    "companies",
]

logger = get_logger(__name__, "elt")


def _get_db_connection():
    connection_string = DATABASE_URL
    if not connection_string:
        raise ValueError("DATABASE_URL is not found")

    engine = create_engine(connection_string, echo=False)
    return engine


def _export_to_parquet():

    timestamp = datetime.datetime.now().strftime("%Y_%m_%d")

    try:
        engine = _get_db_connection()
        exported_files = {}

        output_dir = DATA_COMPLETE_DIR / "db"
        output_dir.mkdir(parents=True, exist_ok=True)

        for table in TABLES:
            logger.info(f"[Load] Reading table: {table}")

            query = text(f"SELECT * FROM {table}")
            with engine.connect() as connection:
                result = connection.execute(query)
                df = pd.DataFrame(result.fetchall(), columns=result.keys())

            if df.empty:
                logger.warning(
                    f"[Load] Warning: Table '{table}' returned no data. Skipping Parquet file."
                )
                continue

            output_file = output_dir / f"{table}_{timestamp}.parquet"

            df.to_parquet(
                output_file,
                engine="pyarrow",
                compression="snappy",
                index=False,
                coerce_timestamps="us",
                allow_truncated_timestamps=True,
            )

            logger.info(
                f"[Load] Exported table: {table} | Row exported: {len(df):,} | Saved to: {output_file.name}"
            )

            exported_files[table] = str(output_file)

        if not exported_files:
            logger.warning(
                "[Load] Warning: No tables were exported (all empty or errors)."
            )

        return exported_files

    except Exception as e:
        logger.error(f"[Load] Error while exporting tables to Parquet: {e}")
        traceback.print_exc()
        sys.exit(1)


def convert_db_to_parquet():
    try:
        _export_to_parquet()

    except Exception as e:
        logger.error(f"[Load] Error: {e}")
        traceback.print_exc()


if __name__ == "__main__":
    convert_db_to_parquet()
