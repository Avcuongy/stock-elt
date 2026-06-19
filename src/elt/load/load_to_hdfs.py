import os
import sys
import logging
import re
from pathlib import Path
from hdfs import InsecureClient
from utils.logger import get_logger
import warnings

warnings.filterwarnings("ignore")

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DATA_DIR = PROJECT_ROOT / "data"
WEBHDFS_URL = "http://hadoop-namenode:9870"
HDFS_USER = "root"
HDFS_BASE_DIR = "/data_lake"

logger = get_logger(__name__, "elt")


def _get_hdfs_client() -> InsecureClient:
    url = os.getenv("WEBHDFS_URL", WEBHDFS_URL)
    user = os.getenv("HDFS_USER", HDFS_USER)

    return InsecureClient(url, user=user)


def _cleanup_old_files(
    client: InsecureClient, local_path: Path, hdfs_target: str
) -> None:
    date_pattern = re.compile(r"(\d{4}_\d{2}_\d{2})")

    if not local_path.is_dir():
        return

    local_files = list(local_path.glob("*.parquet"))
    dates = [
        date_pattern.search(f.name).group(1)
        for f in local_files
        if date_pattern.search(f.name)
    ]

    if not dates:
        return

    latest_date = max(dates)

    for f in local_files:
        match = date_pattern.search(f.name)
        if match and match.group(1) != latest_date:
            f.unlink()

    try:
        if client.status(hdfs_target, strict=False):
            hdfs_files = client.list(hdfs_target)
            for f_name in hdfs_files:
                if not f_name.endswith(".parquet"):
                    continue
                match = date_pattern.search(f_name)
                if match and match.group(1) != latest_date:
                    del_path = f"{hdfs_target}/{f_name}"
                    client.delete(del_path)
        logger.info(
            f"[Load] Cleaned up old files in HDFS: {hdfs_target}, just keeping: {latest_date}"
        )
    except Exception:
        pass


def _upload_parquet_folders(
    client: InsecureClient, local_completed_dir: Path, hdfs_base_dir: str
) -> None:
    mapping = {
        "db": "db",
        "ohlcs": "ohlcs",
    }

    hdfs_base_dir = hdfs_base_dir.rstrip("/") or "/"

    for local_sub, hdfs_sub in mapping.items():
        local_path = local_completed_dir / local_sub
        hdfs_target = (
            f"{hdfs_base_dir}/{hdfs_sub}" if hdfs_base_dir != "/" else f"/{hdfs_sub}"
        )

        _cleanup_old_files(client, local_path, hdfs_target)

        if not local_path.is_dir():
            logger.info(f"[Load] Local directory not found: {local_path}")
            continue

        parquet_files = sorted(local_path.glob("*.parquet"))
        if not parquet_files:
            logger.info(f"[Load] No Parquet files in: {local_path}")
            continue

        client.makedirs(hdfs_target)

        for file_path in parquet_files:
            dest_path = f"{hdfs_target}/{file_path.name}"
            logger.info(f"[Load] Successfully putting {file_path.name} to {dest_path}")

            client.upload(dest_path, str(file_path), overwrite=True)


def load_to_hdfs() -> None:
    local_completed_dir = DATA_DIR / "completed"
    hdfs_base_dir = os.getenv("HDFS_BASE_DIR", HDFS_BASE_DIR)

    logger.info("[Load] Loading Parquet files into HDFS (WebHDFS)")
    logger.info("[Load] Local completed : %s", local_completed_dir)
    logger.info("[Load] HDFS base dir   : %s", hdfs_base_dir)
    logger.info("[Load] WEBHDFS url     : %s", os.getenv("WEBHDFS_URL", WEBHDFS_URL))

    client = _get_hdfs_client()

    _upload_parquet_folders(client, local_completed_dir, hdfs_base_dir)

    logger.info("[Load] HDFS load completed (WebHDFS).")


if __name__ == "__main__":
    load_to_hdfs()
