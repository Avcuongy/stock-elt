from pathlib import Path
import sys
import logging
from backend.load import load_db_others, load_db_exchanges, load_db_companies
import warnings

warnings.filterwarnings("ignore")

PROJECT_ROOT = Path(__file__).resolve().parents[2]
LOGS_DIR = PROJECT_ROOT / "logs" / "backend.log"


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler(LOGS_DIR, mode="a", encoding="utf-8"),
            logging.StreamHandler(sys.stdout),
        ],
    )
    logging.info("[Backend - Load] Start")
    load_db_others()
    load_db_exchanges()
    load_db_companies()
    logging.info("[Backend - Load] Finished")


if __name__ == "__main__":
    main()
