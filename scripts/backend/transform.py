from pathlib import Path
import logging

import warnings

from backend.transform import transform_others, transform_exchanges, transform_companies

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
    logging.info("Transform: Data Source")
    print("[Backend - Transform] Start")
    transform_others()
    transform_exchanges()
    transform_companies()
    print("[Backend - Transform] Finished")
    logging.info("Transform: Finished")


if __name__ == "__main__":
    main()
