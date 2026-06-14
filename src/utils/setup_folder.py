from __future__ import annotations

from pathlib import Path
import logging
import sys
from utils.logger import get_logger

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_ROOT = PROJECT_ROOT / "data"
LOGS_DIR = PROJECT_ROOT / "logs" / "config.log"
DATA_SUBFOLDERS = [
    # completed layer
    "completed/db",
    "completed/ohlcs",
    # processed layer
    "processed/companies",
    "processed/exchanges",
    "processed/industries",
    "processed/regions",
    "processed/sicindustries",
    # raw layer
    "raw/companies",
    "raw/markets",
    "raw/ohlcs",
]

logger = get_logger(__name__, "config")


def _ensure_data_folders() -> None:
    DATA_ROOT.mkdir(exist_ok=True)
    for relative in DATA_SUBFOLDERS:
        folder = DATA_ROOT / relative
        folder.mkdir(parents=True, exist_ok=True)


def setup_folder() -> None:
    logger.info(f"[Config] Make data folders at: {DATA_ROOT}")
    _ensure_data_folders()
    logger.info("[Config] Data folder structure is ready")


if __name__ == "__main__":
    setup_folder()
