from pathlib import Path
import os
import sys
import datetime
import traceback
import pandas as pd
from sqlalchemy import create_engine
from utils.config_env import DATABASE_URL

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DATA_DIR = PROJECT_ROOT / "data"
DATA_RAW_DIR = DATA_DIR / "raw"
DATA_COMPLETE_DIR = DATA_DIR / "complete"
DATABASE_URL = DATABASE_URL


def _get_db_connection():
    connection_string = DATABASE_URL
    if not connection_string:
        raise ValueError("DATABASE_URL is not found")

    engine = create_engine(connection_string, echo=False)
    return engine


def export_to_parquet():

    tables = [
        "regions",
        "exchanges",
        "industries",
        "sicindustries",
        "companies",
    ]

    timestamp = datetime.datetime.now().strftime("%Y_%m_%d")

    try:
        engine = _get_db_connection()

        exported_files = {}

        for table in tables:
            query = f"SELECT * FROM {table}"
            df = pd.read_sql(query, engine)

            if df.empty:
                print(
                    f"[Load] Warning: Table '{table}' returned no data. Skipping Parquet file."
                )
                continue

            output_file = os.path.join(
                DATA_COMPLETE_DIR, f"{table}_{timestamp}.parquet"
            )

            df.to_parquet(
                output_file,
                engine="pyarrow",
                compression="snappy",
                index=False,
            )

            print(f"[Load] Rows exported   : {len(df):,}")
            print(f"[Load] Columns         : {list(df.columns)}")
            print(f"[Load] Saved to        : {output_file}")
            print(
                f"[Load] File size (MB)  : {os.path.getsize(output_file) / (1024 * 1024):.2f}"
            )

            exported_files[table] = output_file

        for tbl, path in exported_files.items():
            print(f"[Load]  - {tbl}: {path}")

        if not exported_files:
            print("[Load] Warning: No tables were exported (all empty or errors).")

        return exported_files

    except Exception as e:
        print(f"[Load] Error while exporting tables to Parquet: {e}")
        traceback.print_exc()
        sys.exit(1)


def convert_db_to_parquet():
    export_to_parquet()


if __name__ == "__main__":
    convert_db_to_parquet()
