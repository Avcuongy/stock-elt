import os
import json
import sys
import traceback
from sqlalchemy import create_engine, text
from sqlalchemy.exc import IntegrityError
from backend.load.load_db_exchanges_2 import DATA_PROCESSED_DIR
from utils.config_env import DATABASE_URL


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


def _load_companies(engine):
    latest_file = _get_latest_file_in_directory(DATA_PROCESSED_DIR, ".json")
    if not latest_file:
        print("[Backend - Load] No processed companies file found.")
        return

    print(f"[Backend - Load] Loading companies from: {latest_file}")

    with open(latest_file, "r", encoding="utf-8") as f:
        companies_data = json.load(f)

    inserted = 0
    updated = 0
    skipped = 0
    errors = 0

    with engine.connect() as conn:
        for idx, company in enumerate(companies_data):
            try:
                company_name = company.get("name")
                ticker = company.get("ticker")
                exchange_name = company.get("exchange")
                industry_name = company.get("industry")
                sector = company.get("sector")
                sic = company.get("sic")
                cik = company.get("cik")
                is_delisted = company.get("isDelisted", False)
                category = company.get("category")
                currency = company.get("currency")
                location = company.get("location")

                if not ticker or not company_name or not cik:
                    print(
                        f"[Load] Skipping company with no ticker, name, or cik: {company}"
                    )
                    skipped += 1
                    continue

                exchange_id = None
                if exchange_name:
                    exchange_query = text("""
                        SELECT exchange_id FROM exchanges WHERE exchange_name = :exchange_name
                    """)
                    result = conn.execute(
                        exchange_query, {"exchange_name": exchange_name}
                    )
                    exchange_row = result.fetchone()

                    if exchange_row:
                        exchange_id = exchange_row[0]
                    else:
                        print(
                            f"[Load] Warning: Exchange '{exchange_name}' not found for company '{ticker}'. Skipping."
                        )
                        errors += 1
                        continue

                industry_id = None
                if industry_name and sector:
                    industry_query = text("""
                        SELECT industry_id FROM industries 
                        WHERE industry_name = :industry_name AND industry_sector = :sector
                    """)
                    result = conn.execute(
                        industry_query,
                        {"industry_name": industry_name, "sector": sector},
                    )
                    industry_row = result.fetchone()

                    if industry_row:
                        industry_id = industry_row[0]

                sic_id = None
                if sic:
                    try:
                        sic_id = int(sic)
                        sic_query = text(
                            "SELECT sic_id FROM sicindustries WHERE sic_id = :sic_id"
                        )
                        result = conn.execute(sic_query, {"sic_id": sic_id})
                        sic_row = result.fetchone()

                        if not sic_row:
                            sic_id = None
                    except (ValueError, TypeError):
                        sic_id = None

                check_query = text("""
                    SELECT company_id FROM companies 
                    WHERE company_ticker = :ticker AND company_is_delisted = :is_delisted
                """)
                result = conn.execute(
                    check_query, {"ticker": ticker, "is_delisted": is_delisted}
                )
                existing = result.fetchone()

                if existing:
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

                    conn.execute(
                        update_sql,
                        {
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
                        },
                    )
                    conn.commit()
                    updated += 1
                else:
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

                    conn.execute(
                        insert_sql,
                        {
                            "name": company_name,
                            "cik": cik,
                            "ticker": ticker,
                            "exchange_id": exchange_id,
                            "industry_id": industry_id,
                            "sic_id": sic_id,
                            "is_delisted": is_delisted,
                            "category": category,
                            "currency": currency,
                            "location": location,
                        },
                    )
                    conn.commit()
                    inserted += 1

                if (idx + 1) % 1000 == 0:
                    print(f"[Load] Processed {idx + 1} companies...")

            except IntegrityError as e:
                skipped += 1
                if skipped <= 10:
                    print(f"[Load] Skipped company {company.get('ticker')}: {e}")
            except Exception as e:
                errors += 1
                if errors <= 10:
                    print(
                        f"[ERROR] Error processing company {company.get('ticker')}: {e}"
                    )

    print(
        f"[Backend - Load] Companies: {inserted} inserted, {updated} updated, {skipped} skipped, {errors} errors"
    )


def load_db_companies():
    print("[Backend - Load] Loading Companies to MySQL")
    try:
        engine = _get_db_connection()
        _load_companies(engine)
    except Exception as e:
        print(f"[Backend - Load] Error: {e}")
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    load_db_companies()
