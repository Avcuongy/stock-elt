from __future__ import annotations

from pathlib import Path
import logging

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_ROOT = PROJECT_ROOT / "data"
DATA_SUBFOLDERS = [
    # completed layer
    "completed/db_to_dl",
    "completed/ohlcs_to_dl",
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


def _ensure_data_folders() -> None:
    """Create the data/ directory structure used by the project.

    This script pre-creates the folders currently present under the top-level
    ``data/`` directory so that pipelines can assume they exist.
    """

    DATA_ROOT.mkdir(exist_ok=True)

    for relative in DATA_SUBFOLDERS:
        folder = DATA_ROOT / relative
        folder.mkdir(parents=True, exist_ok=True)


def setup_folder() -> None:
    print(f"[Config] Make data folders at: {DATA_ROOT}")
    _ensure_data_folders()
    print("[Config] Data folder structure is ready")


if __name__ == "__main__":
    setup_folder()
