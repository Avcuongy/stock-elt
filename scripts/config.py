from pathlib import Path
import logging

import warnings

from utils.setup_folder import setup_folder

warnings.filterwarnings("ignore")

PROJECT_ROOT = Path(__file__).resolve().parents[1]
LOGS_DIR = PROJECT_ROOT / "logs"


def main() -> None:
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="[%(levelname)s] %(message)s",
        filemode="a",
        filename=LOGS_DIR / "config.log",
    )
    logging.info("Configuring data folders")
    setup_folder()
    logging.info("Config setup is complete")


if __name__ == "__main__":
    main()
