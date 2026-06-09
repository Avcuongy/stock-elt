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


def _get_db_connection():
    database_url = DATABASE_URL
    if not database_url:
        raise ValueError("DATABASE_URL not found")

    engine = create_engine(database_url, echo=False)
    return engine


def _load_regions(engine):
    latest_file = _get_latest_file_in_directory(DATA_PROCESSED_DIR / "regions", ".json")
    if not latest_file:
        logging.info("[Backend - Load] No processed regions file found.")
        return

    logging.info(f"[Backend - Load] Loading regions from: {latest_file}")

    with open(latest_file, "r", encoding="utf-8") as f:
        regions_data = json.load(f)

    inserted = 0
    skipped = 0

    with engine.connect() as conn:
        for region in regions_data:
            try:
                local_open = region.get("local_open", "00:00")
                local_close = region.get("local_close", "00:00")

                sql = text("""
                    INSERT INTO regions (region_name, region_local_open, region_local_close)
                    VALUES (:name, :open, :close)
                    ON DUPLICATE KEY UPDATE
                        region_local_open = :open,
                        region_local_close = :close
                """)

                conn.execute(
                    sql,
                    {
                        "name": region.get("region"),
                        "open": local_open,
                        "close": local_close,
                    },
                )
                inserted += 1

            except IntegrityError as e:
                skipped += 1
                logging.info(
                    f"[Backend - Load] Skipped region {region.get('region')}: {e}"
                )
            except Exception as e:
                logging.error(
                    f"[Backend - Load] Error inserting region {region.get('region')}: {e}"
                )
        conn.commit()

    logging.info(
        f"[Backend - Load] Regions: {inserted} inserted/updated, {skipped} skipped"
    )


def _load_industries(engine):
    latest_file = _get_latest_file_in_directory(
        DATA_PROCESSED_DIR / "industries", ".json"
    )
    if not latest_file:
        logging.info("[Backend - Load] No processed industries file found.")
        return

    logging.info(f"[Backend - Load] Loading industries from: {latest_file}")

    with open(latest_file, "r", encoding="utf-8") as f:
        industries_data = json.load(f)

    inserted = 0
    skipped = 0

    with engine.connect() as conn:
        for industry in industries_data:
            try:
                sql = text("""
                    INSERT INTO industries (industry_name, industry_sector)
                    VALUES (:name, :sector)
                    ON DUPLICATE KEY UPDATE
                        industry_sector = :sector
                """)

                conn.execute(
                    sql,
                    {
                        "name": industry.get("industry"),
                        "sector": industry.get("sector"),
                    },
                )

                inserted += 1

            except IntegrityError as e:
                skipped += 1
                logging.info(
                    f"[Backend - Load] Skipped industry {industry.get('industry')}: {e}"
                )
            except Exception as e:
                logging.error(
                    f"[Backend - Load] Error inserting industry {industry.get('industry')}: {e}"
                )
        conn.commit()

    logging.info(
        f"[Backend - Load] Industries: {inserted} inserted/updated, {skipped} skipped"
    )


def _load_sicindustries(engine):
    latest_file = _get_latest_file_in_directory(
        DATA_PROCESSED_DIR / "sicindustries", ".json"
    )

    if not latest_file:
        logging.info("[Backend - Load] No processed sicindustries file found.")
        return

    logging.info(f"[Backend - Load] Loading SIC industries from: {latest_file}")

    with open(latest_file, "r", encoding="utf-8") as f:
        sic_data = json.load(f)

    inserted = 0
    skipped = 0

    with engine.connect() as conn:
        for sic in sic_data:
            try:
                sic_id = sic.get("sic")
                if not sic_id:
                    continue

                sql = text("""
                    INSERT INTO sicindustries (sic_id, sic_industry, sic_sector)
                    VALUES (:sic_id, :industry, :sector)
                    ON DUPLICATE KEY UPDATE
                        sic_industry = :industry,
                        sic_sector = :sector
                """)

                conn.execute(
                    sql,
                    {
                        "sic_id": int(sic_id),
                        "industry": sic.get("sicIndustry"),
                        "sector": sic.get("sicSector"),
                    },
                )
                inserted += 1

            except IntegrityError as e:
                skipped += 1
                logging.info(f"[Backend - Load] Skipped SIC {sic.get('sic')}: {e}")
            except Exception as e:
                logging.error(
                    f"[Backend - Load] Error inserting SIC {sic.get('sic')}: {e}"
                )
        conn.commit()

    logging.info(
        f"[Backend - Load] SIC Industries: {inserted} inserted/updated, {skipped} skipped"
    )


def load_db_others():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler(LOGS_DIR, mode="a", encoding="utf-8"),
            logging.StreamHandler(sys.stdout),
        ],
    )
    logging.info(
        "[Backend - Load] Loading Regions + Industries + SIC Industries to MySQL"
    )
    try:
        engine = _get_db_connection()
        _load_regions(engine)
        _load_industries(engine)
        _load_sicindustries(engine)
    except Exception as e:
        logging.error(f"[Backend - Load] Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    load_db_others()
