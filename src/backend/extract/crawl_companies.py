from pathlib import Path
import sys
import requests
import json
import datetime
from utils.logger import get_logger
from utils.config_env import SEC_API_KEY

PROJECT_ROOT = Path(__file__).resolve().parents[3]
EXCHANGES = ["nasdaq", "nyse"]
COMPANY_LIMIT = 100

logger = get_logger(__name__, "backend")


def crawl_companies():
    """
    Crawl company data from SEC API for NYSE and NASDAQ.
    Saves data to data/raw/companies/crawl_companies_{date}.json
    """
    list_companies = []

    limit_per_exchange = (
        COMPANY_LIMIT // len(EXCHANGES) if COMPANY_LIMIT and COMPANY_LIMIT > 0 else None
    )

    for exchange in EXCHANGES:
        try:
            url = f"https://api.sec-api.io/mapping/exchange/{exchange}?token={SEC_API_KEY}"
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()

            if limit_per_exchange:
                data = data[:limit_per_exchange]

            list_companies.extend(data)
            logger.info(
                f"[Backend - Extract] Extracted {len(data)} companies from the {exchange.upper()} stock exchange."
            )
        except Exception as e:
            logger.error(
                f"[Backend - Extract] Error crawling exchange {exchange.upper()}: {e}"
            )

    yesterday = datetime.date.today() - datetime.timedelta(days=1)
    date_str = yesterday.strftime("%Y_%m_%d")

    output_dir = PROJECT_ROOT / "data" / "raw" / "companies"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"crawl_companies_{date_str}.json"

    with open(output_path, "w", encoding="utf-8") as outfile:
        json.dump(list_companies, outfile, indent=4, ensure_ascii=False)

    logger.info(
        f"[Backend - Extract] Successfully saved a total of {len(list_companies)} companies to {output_path.name}"
    )
    return output_path


if __name__ == "__main__":
    crawl_companies()
