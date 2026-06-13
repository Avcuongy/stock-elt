from pathlib import Path
import os
import sys
import logging
import traceback
import duckdb
from pyspark.shell import spark
from pyspark.sql import SparkSession
from pyspark.sql.functions import trim, lower
from pyspark.sql.functions import (
    col,
    to_date,
    date_format,
    dayofmonth,
    month,
    year,
    quarter,
    dayofweek,
    weekofyear,
    when,
    lit,
)
from utils.logger import get_logger
import warnings

warnings.filterwarnings("ignore")

PROJECT_ROOT = Path(__file__).resolve().parents[3]
LOGS_DIR = PROJECT_ROOT / "logs" / "elt.log"
DATA_DIR = PROJECT_ROOT / "data"
DUCKDB_PATH = PROJECT_ROOT / "data_warehouse.duckdb"
HDFS_RPC_URL = "hdfs://localhost:9000"
HDFS_BASE_DIR = "/data_lake"
HDFS_DB_DIR = f"{HDFS_RPC_URL}{HDFS_BASE_DIR}/db"
HDFS_OHLCS_DIR = f"{HDFS_RPC_URL}{HDFS_BASE_DIR}/ohlcs"

logger = get_logger(__name__, "elt")


def _get_spark_session():
    return (
        SparkSession.builder.appName("elt_transform")
        .config("spark.hadoop.dfs.client.use.datanode.hostname", "true")
        .getOrCreate()
    )


def _build_dim_date(raw_ohlcs):
    dim_date = raw_ohlcs.select(to_date(col("timestamp")).alias("full_date")).distinct()

    dim_date = (
        dim_date.withColumn(
            "date_key", date_format(col("full_date"), "yyyyMMdd").cast("int")
        )
        .withColumn("day", dayofmonth(col("full_date")))
        .withColumn("month", month(col("full_date")))
        .withColumn("year", year(col("full_date")))
        .withColumn("quarter", quarter(col("full_date")))
        .withColumn("day_of_week", date_format(col("full_date"), "EEEE"))
        .withColumn("week_of_year", weekofyear(col("full_date")))
        .withColumn(
            "is_weekend",
            when(dayofweek(col("full_date")).isin([1, 7]), True).otherwise(False),
        )
        .withColumn("is_holiday", lit(False))
    )

    return dim_date


def _build_fact_stock_daily(
    raw_ohlcs,
    raw_companies,
    raw_exchanges,
    raw_industries,
    dim_company_db,
    dim_exchange_db,
    dim_industry_db,
):
    fact_df = (
        raw_ohlcs.withColumn("full_date", to_date(col("timestamp")))
        .withColumn("date_key", date_format(col("full_date"), "yyyyMMdd").cast("int"))
        .withColumn("price_change", col("close") - col("open"))
        .withColumn(
            "price_trend",
            when(col("price_change") > 0, "up")
            .when(col("price_change") < 0, "down")
            .otherwise("unchanged"),
        )
        .withColumn("ticker", trim(lower(col("ticker"))))
    )

    bridge_df = raw_companies.select(
        trim(lower(col("company_ticker"))).alias("bridge_ticker"),
        col("company_exchange_id").alias("bridge_exchange_id"),
        col("company_industry_id").alias("bridge_industry_id"),
        "company_category",
    )
    fact_joined = fact_df.join(
        bridge_df, fact_df.ticker == bridge_df.bridge_ticker, "inner"
    )

    dim_company_db = dim_company_db.withColumn(
        "company_ticker", trim(lower(col("company_ticker")))
    )
    fact_joined = fact_joined.join(
        dim_company_db, fact_joined.ticker == dim_company_db.company_ticker, "inner"
    )

    exchange_bridge = raw_exchanges.select(
        col("exchange_id").alias("bridge_exchange_ref_id"),
        trim(col("exchange_name")).alias("bridge_exchange_name"),
    )
    fact_joined = fact_joined.join(
        exchange_bridge,
        fact_joined.bridge_exchange_id == exchange_bridge.bridge_exchange_ref_id,
        "inner",
    )

    dim_exchange_db = dim_exchange_db.withColumn(
        "exchange_name", trim(col("exchange_name"))
    )
    fact_joined = fact_joined.join(
        dim_exchange_db,
        fact_joined.bridge_exchange_name == dim_exchange_db.exchange_name,
        "inner",
    )

    industry_bridge = raw_industries.select(
        col("industry_id").alias("bridge_industry_ref_id"),
        trim(col("industry_name")).alias("bridge_industry_name"),
    )
    fact_joined = fact_joined.join(
        industry_bridge,
        fact_joined.bridge_industry_id == industry_bridge.bridge_industry_ref_id,
        "inner",
    )

    dim_industry_db = dim_industry_db.withColumn(
        "industry_name", trim(col("industry_name"))
    )
    fact_joined = fact_joined.join(
        dim_industry_db,
        (fact_joined.bridge_industry_name == dim_industry_db.industry_name)
        & (fact_joined.company_category == dim_industry_db.company_category),
        "inner",
    )

    fact_final = fact_joined.select(
        col("date_key"),
        col("company_key").cast("int"),
        col("industry_key").cast("int"),
        col("exchange_key").cast("int"),
        col("open").alias("open_price"),
        col("high").alias("high_price"),
        col("low").alias("low_price"),
        col("close").alias("close_price"),
        col("volume").cast("long"),
        col("price_change"),
        col("price_trend"),
    )

    fact_final = fact_final.filter(
        col("company_key").isNotNull()
        & col("industry_key").isNotNull()
        & col("exchange_key").isNotNull()
    )

    fact_final = fact_final.dropDuplicates()

    return fact_final


def transform_2(spark: SparkSession = None, target_date: str = None):
    should_stop_spark = False
    if spark is None:
        spark = _get_spark_session()
        should_stop_spark = True

    file_pattern = f"ohlcs_{target_date}.parquet" if target_date else "ohlcs_*.parquet"
    raw_ohlcs = spark.read.parquet(f"{HDFS_OHLCS_DIR}/{file_pattern}")
    raw_companies = spark.read.parquet(f"{HDFS_DB_DIR}/companies_*.parquet")
    raw_exchanges = spark.read.parquet(f"{HDFS_DB_DIR}/exchanges_*.parquet")
    raw_industries = spark.read.parquet(f"{HDFS_DB_DIR}/industries_*.parquet")

    try:
        with duckdb.connect(str(DUCKDB_PATH)) as conn:
            conn.execute("SET schema = 'DataWarehouse'")

            dim_company_db = spark.createDataFrame(
                conn.execute(
                    "SELECT company_key, company_ticker FROM DIM_COMPANY WHERE is_current = TRUE"
                ).df()
            )

            dim_exchange_db = spark.createDataFrame(
                conn.execute(
                    "SELECT exchange_key, exchange_name FROM DIM_EXCHANGE WHERE is_current = TRUE"
                ).df()
            )

            dim_industry_db = spark.createDataFrame(conn.execute("""
                    SELECT 
                        industry_key, 
                        industry_name, 
                        company_category 
                    FROM DIM_INDUSTRY 
                    WHERE is_current = TRUE
                    """).df())

        df_dim_date = _build_dim_date(raw_ohlcs)
        df_fact = _build_fact_stock_daily(
            raw_ohlcs,
            raw_companies,
            raw_exchanges,
            raw_industries,
            dim_company_db,
            dim_exchange_db,
            dim_industry_db,
        )

        pd_dim_date = df_dim_date.toPandas()
        pd_fact = df_fact.toPandas()
        pd_fact = pd_fact.dropna(subset=["company_key", "industry_key", "exchange_key"])

        if pd_fact[["company_key", "industry_key", "exchange_key"]].isna().any().any():
            raise ValueError("Found NULL foreign keys in FACT_STOCK_DAILY")

        with duckdb.connect(str(DUCKDB_PATH)) as conn:
            conn.execute("SET schema = 'DataWarehouse'")

            conn.execute("""
                INSERT INTO DIM_DATE (date_key, full_date, day, month, year, quarter, day_of_week, week_of_year, is_weekend, is_holiday)
                SELECT date_key, full_date, day, month, year, quarter, day_of_week, week_of_year, is_weekend, is_holiday FROM pd_dim_date
                ON CONFLICT (date_key) DO NOTHING
            """)

            conn.execute("""
                INSERT INTO FACT_STOCK_DAILY 
                (date_key, company_key, industry_key, exchange_key, open_price, high_price, low_price, close_price, volume, price_change, price_trend)
                SELECT date_key, company_key, industry_key, exchange_key, open_price, high_price, low_price, close_price, volume, price_change, price_trend 
                FROM pd_fact
            """)

            date_count = conn.execute("SELECT COUNT(*) FROM DIM_DATE").fetchone()[0]
            fact_count = conn.execute(
                "SELECT COUNT(*) FROM FACT_STOCK_DAILY"
            ).fetchone()[0]

        logger.info(f"[Transform] DIM_DATE records : {date_count:,}")
        logger.info(f"[Transform] FACT_STOCK_DAILY records: {fact_count:,}")
        logger.info(
            "[Transform] Successfully transformed dim_date, fact_stock_daily and loaded into DuckDB"
        )

    except Exception as e:
        logger.error(f"[Transform] Error during transform_2 processing flow: {e}")
        traceback.print_exc()

    finally:
        if should_stop_spark:
            spark.stop()


if __name__ == "__main__":
    transform_2()
