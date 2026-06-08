import datetime
import json
from pathlib import Path
from typing import Optional

import requests

from utils.config_env import MASSIVE_API_KEY

API_KEY = MASSIVE_API_KEY
ADJUSTED = "true"
INCLUDE_OTC = "true"
BASE_URL = "https://api.polygon.io/v2/aggs/grouped/locale/us/market/stocks"


def get_target_date(delta_days: int = 1) -> datetime.date:
    """Return the target date, default is yesterday."""
    return datetime.date.today() - datetime.timedelta(days=delta_days)


def build_url(trading_date: datetime.date) -> str:
    """Build Polygon OHLCs API URL for a given trading date."""
    date_str = trading_date.strftime("%Y-%m-%d")
    return (
        f"{BASE_URL}/{date_str}?adjusted={ADJUSTED}"
        f"&include_otc={INCLUDE_OTC}&apiKey={API_KEY}"
    )


def get_output_path(trading_date: datetime.date) -> Path:
    """Return output path under data/raw/ohlcs for the given date."""
    date_str = trading_date.strftime("%Y_%m_%d")
    project_root = Path(__file__).resolve().parents[3]
    output_dir = project_root / "data" / "raw" / "ohlcs"
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir / f"crawl_ohlcs_{date_str}.json"


def crawl_ohlcs(trading_date: Optional[datetime.date] = None) -> Path:
    """Crawl OHLCs data for the given date (default: yesterday) and save to JSON.

    Returns the path to the saved file.
    """
    if trading_date is None:
        trading_date = get_target_date(1)

    url = build_url(trading_date)
    response = requests.get(url, timeout=60)
    response.raise_for_status()
    payload = response.json()
    results = payload.get("results", [])

    output_path = get_output_path(trading_date)
    with output_path.open("w", encoding="utf-8") as outfile:
        json.dump(results, outfile, indent=4)

    print(f"The process of crawling {len(results)} OHLCs was successful")
    print(f"Saving at {output_path}")
    return output_path


if __name__ == "__main__":
    crawl_ohlcs()
