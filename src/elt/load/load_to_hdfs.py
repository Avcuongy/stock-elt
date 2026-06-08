from __future__ import annotations

import os
from pathlib import Path

from hdfs import InsecureClient
from utils import HDFS_BASE_DIR


def get_hdfs_client() -> InsecureClient:
    """Create a WebHDFS client using environment variables.

    Expected env vars (with defaults):
    - WebHDFS URL: http://localhost:9870
    - HDFS_USER: HDFS user (default: "root")
    """

    url = "http://localhost:9870"
    user = "root"

    return InsecureClient(url, user=user)


def upload_parquet_folders(
    client: InsecureClient, local_completed_dir: Path, hdfs_base_dir: str
) -> None:
    """Upload local Parquet files under data/completed to HDFS via WebHDFS.

    Mirrors the behavior of load_parquet_to_hdfs.sh:
      - db_to_dl   -> <HDFS_BASE_DIR>/db
      - news_to_dl -> <HDFS_BASE_DIR>/news
      - ohlcs_to_dl-> <HDFS_BASE_DIR>/ohlcs
      - markets_to_dl -> <HDFS_BASE_DIR>/markets
    """

    mapping = {
        "db_to_dl": "db",
        "news_to_dl": "news",
        "ohlcs_to_dl": "ohlcs",
        "markets_to_dl": "markets",
    }

    hdfs_base_dir = hdfs_base_dir.rstrip("/") or "/"

    for local_sub, hdfs_sub in mapping.items():
        local_path = local_completed_dir / local_sub
        hdfs_target = (
            f"{hdfs_base_dir}/{hdfs_sub}" if hdfs_base_dir != "/" else f"/{hdfs_sub}"
        )

        if not local_path.is_dir():
            print(f"[SKIP] Local directory not found: {local_path}")
            continue

        parquet_files = sorted(local_path.glob("*.parquet"))
        if not parquet_files:
            print(f"[SKIP] No Parquet files in: {local_path}")
            continue

        print(f"\nUploading from {local_path} to {hdfs_target}")

        # Ensure target directory exists
        client.makedirs(hdfs_target)

        for file_path in parquet_files:
            dest_path = f"{hdfs_target}/{file_path.name}"
            print(f"  -> Putting {file_path.name} -> {dest_path}")
            # overwrite=True to mirror `hdfs dfs -put -f`
            client.upload(hdfs_target, str(file_path), overwrite=True)


def main() -> None:
    base_dir = Path(__file__).resolve().parents[3]
    local_completed_dir = base_dir / "data" / "completed"
    hdfs_base_dir = f"{HDFS_BASE_DIR}"

    print("=" * 45)
    print("Loading Parquet files into HDFS (WebHDFS)")
    print("Project root:    ", base_dir)
    print("Local completed: ", local_completed_dir)
    print("HDFS base dir:   ", hdfs_base_dir)
    print("WEBHDFS url:     ", "http://localhost:9870")
    print("=" * 45)

    client = get_hdfs_client()

    upload_parquet_folders(client, local_completed_dir, hdfs_base_dir)

    print("\n" + "=" * 45)
    print("HDFS load completed (WebHDFS).")
    print("=" * 45)


if __name__ == "__main__":
    main()
