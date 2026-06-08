import os
from dotenv import load_dotenv

load_dotenv()

# API Configuration
SEC_API_KEY = os.getenv("SEC_API_KEY")
ALPHAVANTAGE_API_KEY = os.getenv("ALPHAVANTAGE_API_KEY")
MASSIVE_API_KEY = os.getenv("MASSIVE_API_KEY")

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL")

# Hadoop configuration
HDFS_DEFAULT_FS = os.getenv("HDFS_DEFAULT_FS")
HDFS_BASE_DIR = os.getenv("HDFS_BASE_DIR")
HDFS_USER = os.getenv("HDFS_USER")
