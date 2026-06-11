from pathlib import Path
import os
import sys
import logging
from backend.extract import crawl_markets, crawl_companies
from utils.logger import get_logger

import warnings

warnings.filterwarnings("ignore")

logger = get_logger(__name__, "backend")


def main() -> None:
    logger.info("[Backend - Extract] Start")
    crawl_markets()
    crawl_companies()
    logger.info("[Backend - Extract] Finished")


if __name__ == "__main__":
    main()
