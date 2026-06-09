from pathlib import Path
import sys
import requests
import json
import datetime
import logging
from utils.config_env import SEC_API_KEY

PROJECT_ROOT = Path(__file__).resolve().parents[3]
LOGS_DIR = PROJECT_ROOT / "logs" / "backend.log"
SEC_API_KEY = SEC_API_KEY
EXCHANGES = ["nasdaq", "nyse"]
COMPANY_LIMIT = 1000


def crawl_companies():
    """
    Crawl company data from SEC API for NYSE and NASDAQ.
    Saves data to ./data/raw/companies/crawl_companies_{date}.json
    """
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler(LOGS_DIR, mode="a", encoding="utf-8"),
            logging.StreamHandler(sys.stdout),
        ],
    )

    list_companies = []

    for exchange in EXCHANGES:
        url = f"https://api.sec-api.io/mapping/exchange/{exchange}?token={SEC_API_KEY}"
        response = requests.get(url)
        data = response.json()
        list_companies.extend(data)
        logging.info(
            f"[Backend - Extract] Extracted {len(data)} companies from the {exchange.upper()} stock exchange."
        )

    if COMPANY_LIMIT and COMPANY_LIMIT > 0:
        list_companies = list_companies[:COMPANY_LIMIT]
    json_payload = json.dumps(list_companies, indent=4)

    # Get yesterday's date
    yesterday = datetime.date.today() - datetime.timedelta(days=1)
    date_str = yesterday.strftime("%Y_%m_%d")

    path = f"./data/raw/companies/crawl_companies_{date_str}.json"
    with open(path, "w") as outfile:
        outfile.write(json_payload)

    logging.info(
        f"[Backend - Extract] Successfully saved {len(list_companies)} companies to {path}"
    )
    return path


if __name__ == "__main__":
    crawl_companies()
