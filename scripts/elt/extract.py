from pathlib import Path
import sys
import logging
from elt.extract import crawl_ohlcs
from utils.logger import get_logger
import warnings

warnings.filterwarnings("ignore")


logger = get_logger(__name__, "elt")


def main() -> None:
    logger.info("[Extract] Start")
    crawl_ohlcs()
    logger.info("[Extract] Finished")


if __name__ == "__main__":
    main()
