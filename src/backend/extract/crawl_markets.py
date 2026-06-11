from pathlib import Path
import sys
import logging
import requests
import json
import datetime
from utils.config_env import ALPHAVANTAGE_API_KEY
from utils.logger import get_logger

PROJECT_ROOT = Path(__file__).resolve().parents[3]
API_KEY = ALPHAVANTAGE_API_KEY
FUNCTION = "MARKET_STATUS"


logger = get_logger(__name__, "backend")


def crawl_markets():
    """
    Crawl market status data from Alpha Vantage API.
    Saves data to ./data/raw/markets/crawl_markets_{date}.json
    """
    url = f"https://www.alphavantage.co/query?function={FUNCTION}&apikey={API_KEY}"

    response = requests.get(url)
    data = response.json().get("markets", [])

    json_payload = json.dumps(data, indent=4)

    # Get yesterday's date
    yesterday = datetime.date.today() - datetime.timedelta(days=1)
    date_str = yesterday.strftime("%Y_%m_%d")

    path = f"./data/raw/markets/crawl_markets_{date_str}.json"
    with open(path, "w") as outfile:
        outfile.write(json_payload)

    logger.info(
        f"[Backend - Extract] Successfully saved {len(data)} regions and exchanges to {path}"
    )
    return path


if __name__ == "__main__":
    crawl_markets()
