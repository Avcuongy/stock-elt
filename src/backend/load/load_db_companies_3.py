import datetime
import json
import logging
import os
import sys
import traceback
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


def _load_companies(engine):
    latest_file = _get_latest_file_in_directory(
        DATA_PROCESSED_DIR / "companies", ".json"
    )
    if not latest_file:
        logger.info("[Backend - Load] No processed companies file found.")
        return

    logger.info(f"[Backend - Load] Loading companies from: {latest_file}")

    with open(latest_file, "r", encoding="utf-8") as f:
        companies_data = json.load(f)

    inserted = 0
    updated = 0
    skipped = 0
    errors = 0

    update_sql = text("""
        UPDATE companies SET
            company_name = :name,
            company_cik = :cik,
            company_exchange_id = :exchange_id,
            company_industry_id = :industry_id,
            company_sic_id = :sic_id,
            company_category = :category,
            company_currency = :currency,
            company_location = :location
        WHERE company_ticker = :ticker AND company_is_delisted = :is_delisted
    """)

    insert_sql = text("""
        INSERT INTO companies (
            company_name, company_cik, company_ticker, company_exchange_id,
            company_industry_id, company_sic_id, company_is_delisted,
            company_category, company_currency, company_location
        )
        VALUES (
            :name, :cik, :ticker, :exchange_id,
            :industry_id, :sic_id, :is_delisted,
            :category, :currency, :location
        )
    """)

    with engine.begin() as conn:
        exchange_map = {}
        res = conn.execute(text("SELECT exchange_name, exchange_id FROM exchanges"))
        for row in res.fetchall():
            exchange_map[row[0]] = row[1]

        industry_map = {}
        res = conn.execute(
            text("SELECT industry_name, industry_sector, industry_id FROM industries")
        )
        for row in res.fetchall():
            industry_map[(row[0], row[1])] = row[2]

        sic_set = set()
        res = conn.execute(text("SELECT sic_id FROM sicindustries"))
        for row in res.fetchall():
            sic_set.add(row[0])

        existing_companies = set()
        res = conn.execute(
            text("SELECT company_ticker, company_is_delisted FROM companies")
        )
        for row in res.fetchall():
            existing_companies.add((row[0], bool(row[1])))

        for idx, company in enumerate(companies_data):
            try:
                company_name = company.get("name")
                ticker = company.get("ticker")
                exchange_name = company.get("exchange")
                industry_name = company.get("industry")
                sector = company.get("sector")
                sic = company.get("sic")
                cik = company.get("cik")
                is_delisted = bool(company.get("isDelisted", False))
                category = company.get("category")
                currency = company.get("currency")
                location = company.get("location")

                if not ticker or not company_name or not cik:
                    logger.warning(
                        f"[Backend - Load] Skipping company with no ticker, name, or cik: {company}"
                    )
                    skipped += 1
                    continue

                exchange_id = exchange_map.get(exchange_name)
                if exchange_name and not exchange_id:
                    logger.warning(
                        f"[Backend - Load] Warning: Exchange '{exchange_name}' not found in DB for company '{ticker}'. Skipping."
                    )
                    errors += 1
                    continue

                industry_id = industry_map.get((industry_name, sector))

                sic_id = None
                if sic:
                    try:
                        temp_sic = int(sic)
                        if temp_sic in sic_set:
                            sic_id = temp_sic
                    except (ValueError, TypeError):
                        pass

                params = {
                    "name": company_name,
                    "cik": cik,
                    "exchange_id": exchange_id,
                    "industry_id": industry_id,
                    "sic_id": sic_id,
                    "category": category,
                    "currency": currency,
                    "location": location,
                    "ticker": ticker,
                    "is_delisted": is_delisted,
                }

                if (ticker, is_delisted) in existing_companies:
                    conn.execute(update_sql, params)
                    updated += 1
                else:
                    conn.execute(insert_sql, params)
                    inserted += 1

                if (idx + 1) % 1000 == 0:
                    logger.info(f"[Backend - Load] Processed {idx + 1} companies...")

            except IntegrityError as e:
                skipped += 1
                if skipped <= 10:
                    logger.warning(
                        f"[Backend - Load] Skipped company {company.get('ticker')} (IntegrityError): {e}"
                    )
            except Exception as e:
                errors += 1
                if errors <= 10:
                    logger.error(
                        f"[Backend - Load] Error processing company {company.get('ticker')}: {e}"
                    )

    logger.info(
        f"[Backend - Load] Companies: {inserted} inserted, {updated} updated, {skipped} skipped, {errors} errors"
    )


def load_db_companies():
    logger.info("[Backend - Load] Loading Companies to database")
    try:
        engine = _get_db_connection()
        _load_companies(engine)
    except Exception as e:
        logger.error(f"[Backend - Load] Error: {e}")
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    load_db_companies()
