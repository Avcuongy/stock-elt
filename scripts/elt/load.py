from pathlib import Path
import logging
import sys
from elt.load import convert_db_to_parquet, convert_api_to_parquet, load_to_hdfs
import warnings

warnings.filterwarnings("ignore")

PROJECT_ROOT = Path(__file__).resolve().parents[2]
LOGS_DIR = PROJECT_ROOT / "logs" / "elt.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOGS_DIR, mode="a", encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)


def main() -> None:
    logger.info("[Load] ETL Start")
    convert_db_to_parquet()
    convert_api_to_parquet()
    load_to_hdfs()
    logger.info("[Load] ETL Finished")


if __name__ == "__main__":
    main()
