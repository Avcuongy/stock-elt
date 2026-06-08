from pathlib import Path
import logging
from backend.extract import crawl_markets, crawl_companies

import warnings

warnings.filterwarnings("ignore")

PROJECT_ROOT = Path(__file__).resolve().parents[2]
LOGS_DIR = PROJECT_ROOT / "logs"


def main() -> None:
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="[%(levelname)s] %(message)s",
        filemode="a",
        filename=LOGS_DIR / "backend.log",
    )
    logging.info("Extract: Data Source")
    print("[Backend - Extract] Start")
    crawl_markets()
    crawl_companies()
    print("[Backend - Extract] Finished")
    logging.info("Extract: Finished")


if __name__ == "__main__":
    main()
