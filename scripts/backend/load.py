from pathlib import Path
import logging

import warnings

from backend.load import load_db_others, load_db_exchanges, load_db_companies

warnings.filterwarnings("ignore")

PROJECT_ROOT = Path(__file__).resolve().parents[2]
LOGS_DIR = PROJECT_ROOT / "logs"


def main() -> None:
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="[%(levelname)s] %(message)s",
        filemode="a",
        filename=LOGS_DIR / "Backend.log",
    )
    logging.info("Load: Data Source")
    print("[Backend - Load] Start")
    load_db_others()
    load_db_exchanges()
    load_db_companies()
    print("[Backend - Load] Finished")
    logging.info("Load: Finished")


if __name__ == "__main__":
    main()
