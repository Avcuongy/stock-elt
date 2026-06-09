import sys
import datetime
import json
import pytz
import logging
from pathlib import Path
from massive import RESTClient
from utils.config_env import MASSIVE_API_KEY

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DATA_DIR = PROJECT_ROOT / "data"
DATA_RAW_DIR = DATA_DIR / "raw"
LOGS_DIR = PROJECT_ROOT / "logs" / "elt.log"


def _get_target_date(delta_days: int = 1) -> datetime.date:
    ny_tz = pytz.timezone("America/New_York")
    ny_today = datetime.datetime.now(ny_tz).date()
    target_date = ny_today - datetime.timedelta(days=delta_days)
    if target_date.weekday() == 5:
        target_date -= datetime.timedelta(days=1)
    elif target_date.weekday() == 6:
        target_date -= datetime.timedelta(days=2)

    return target_date


def _get_output_path(trading_date: datetime.date) -> Path:
    date_str = trading_date.strftime("%Y_%m_%d")
    project_root = Path(__file__).resolve().parents[3]
    output_dir = project_root / "data" / "raw" / "ohlcs"
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir / f"crawl_ohlcs_{date_str}.json"


def crawl_ohlcs():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler(LOGS_DIR, mode="a", encoding="utf-8"),
            logging.StreamHandler(sys.stdout),
        ],
    )
    target_date = _get_target_date(delta_days=1)
    date_str = target_date.strftime("%Y-%m-%d")

    client = RESTClient(MASSIVE_API_KEY)

    try:
        grouped_data = client.get_grouped_daily_aggs(date_str, adjusted="true")

        results = [item.__dict__ for item in grouped_data]

        output_path = _get_output_path(target_date)
        with output_path.open("w", encoding="utf-8") as outfile:
            json.dump(results, outfile, indent=4)

        logging.info(
            f"[Extract] Successful crawling {len(results)} OHLCs to {output_path}"
        )
        return output_path

    except Exception as e:
        logging.error(f"[Extract] Error: {e}")
        return None


if __name__ == "__main__":
    crawl_ohlcs()
