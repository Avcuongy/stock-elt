from pathlib import Path
import duckdb
import logging
from utils.logger import get_logger

PROJECT_ROOT = Path(__file__).resolve().parents[2]
database_path = PROJECT_ROOT / "data_warehouse.duckdb"

logger = get_logger(__name__, "config")


def config_dw() -> None:
    if database_path.exists():
        database_path.unlink()

    conn = duckdb.connect(database=database_path)

    sql_file_path = PROJECT_ROOT / "config" / "data_warehouse.sql"
    with open(sql_file_path, "r", encoding="utf-8") as file:
        sql_script = file.read()

    conn.execute(sql_script)
    logger.info(f"[Config] Setup data warehouse at {database_path}")
    conn.close()


if __name__ == "__main__":
    config_dw()
