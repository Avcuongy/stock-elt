"""
dim_date, dim_company
"""

from __future__ import annotations

from pathlib import Path

import duckdb
import pandas as pd
from pyspark.sql import SparkSession
from pyspark.sql import functions as F

from utils.config_env import HDFS_BASE_DIR, HDFS_DEFAULT_FS


REPO_ROOT = Path(__file__).resolve().parents[3]
DUCKDB_PATH = REPO_ROOT / "data_warehouse.duckdb"


def _require_hdfs_config() -> None:
    """Validate that HDFS-related configuration is present.

    Tables in DuckDB are assumed to be created beforehand; this ETL step
    only loads data into existing tables and does not create or modify
    schemas.
    """

    if not HDFS_BASE_DIR:
        raise ValueError("HDFS_BASE_DIR is not set in environment/.env")

    # HDFS_DEFAULT_FS may be empty if Spark core-site.xml is used.
    # In that case we will build absolute paths that rely on cluster
    # defaults (e.g. "/financial_de/ohlcs").


def _build_hdfs_path(subdir: str) -> str:
    """Build an HDFS path to a logical sub-directory under HDFS_BASE_DIR.

    Examples
    --------
    - HDFS_DEFAULT_FS = "hdfs://namenode:8020"
      HDFS_BASE_DIR   = "/financial_de"
      subdir          = "ohlcs"
      -> "hdfs://namenode:8020/financial_de/ohlcs"

    - HDFS_DEFAULT_FS = "" (use cluster defaults)
      HDFS_BASE_DIR   = "/financial_de"
      subdir          = "db"
      -> "/financial_de/db"
    """

    base_dir = HDFS_BASE_DIR.rstrip("/")
    if HDFS_DEFAULT_FS:
        default_fs = HDFS_DEFAULT_FS.rstrip("/")
        return f"{default_fs}{base_dir}/{subdir}"
    return f"{base_dir}/{subdir}"


def _get_spark_session() -> SparkSession:
    """Create or get a SparkSession configured for HDFS access."""

    spark = (
        SparkSession.builder.appName("elt_dim_date_company")
        .config("spark.hadoop.fs.defaultFS", HDFS_DEFAULT_FS)
        .config("spark.hadoop.dfs.client.use.datanode.hostname", "true")
        .getOrCreate()
    )
    return spark


def _build_dim_date(spark: SparkSession, con: duckdb.DuckDBPyConnection) -> None:
    """Populate DIM_DATE from both OHLC and news on HDFS.

    Logic:
    - Read OHLC parquet from HDFS ("timestamp" column).
    - Read news parquet from HDFS ("time_published" string column).
    - Chuẩn hoá cả hai về full_date (DATE), union và distinct.
    - Tính year, month, quarter, date_key (YYYYMMDD) từ full_date.
    - Full refresh: truncate và insert lại toàn bộ.
    """

    news_path = _build_hdfs_path("news")
    ohlc_path = _build_hdfs_path("ohlcs")

    # 1) Ngày từ news.time_published
    print(f"[DIM_DATE] Reading news data from: {news_path}")
    news_df = spark.read.parquet(news_path)

    if "time_published" not in news_df.columns:
        raise ValueError(
            "Expected column 'time_published' in news parquet, but it was not found."
        )

    dates_news = (
        news_df.select("time_published")
        .dropna()
        .withColumn(
            "full_date",
            F.to_date(F.to_timestamp("time_published", "yyyyMMdd'T'HHmmss")),
        )
        .select("full_date")
        .dropna()
        .dropDuplicates()
    )

    # 2) Ngày từ OHLC.timestamp
    print(f"[DIM_DATE] Reading OHLC data from: {ohlc_path}")
    ohlc_df = spark.read.parquet(ohlc_path)

    if "timestamp" not in ohlc_df.columns:
        raise ValueError(
            "Expected column 'timestamp' in OHLC parquet, but it was not found."
        )

    dates_ohlc = (
        ohlc_df.select("timestamp")
        .dropna()
        .withColumn("full_date", F.to_date("timestamp"))
        .select("full_date")
        .dropna()
        .dropDuplicates()
    )

    # 3) Union hai nguồn ngày
    dates_df = dates_news.unionByName(dates_ohlc).dropDuplicates(["full_date"])

    # Tính các trường calendar
    dates_df = (
        dates_df.withColumn("year", F.year("full_date"))
        .withColumn("month", F.month("full_date"))
        .withColumn("quarter", F.quarter("full_date"))
        .withColumn(
            "date_key",
            (
                F.col("year") * F.lit(10000)
                + F.col("month") * F.lit(100)
                + F.dayofmonth("full_date")
            ).cast("int"),
        )
    )

    pdf = dates_df.toPandas()
    if pdf.empty:
        print("[DIM_DATE] No dates found in OHLC/news sources; skipping.")
        return

    # Ensure correct dtypes for DuckDB
    pdf["full_date"] = pd.to_datetime(pdf["full_date"]).dt.date

    print(f"[DIM_DATE] Loading {len(pdf)} rows into DuckDB")
    con.register("df_dim_date", pdf)
    con.execute(
        """
		INSERT OR REPLACE INTO dim_date (date_key, full_date, month, quarter, year)
		SELECT date_key, full_date, month, quarter, year
		FROM df_dim_date
		"""
    )
    con.unregister("df_dim_date")


def _build_dim_company(spark: SparkSession, con: duckdb.DuckDBPyConnection) -> None:
    """Populate DIM_COMPANY by joining normalized DB tables from HDFS.

    Sources (all exported to Parquet and uploaded to HDFS under
    ``<HDFS_BASE_DIR>/db``):

    - companies      (companies_*.parquet)
    - exchanges      (exchanges_*.parquet)
    - industries     (industries_*.parquet)
    - sicindustries  (sicindustries_*.parquet)

    Mapping to DIM_COMPANY columns:
    - company_key          <- companies.company_id
    - company_ticker       <- companies.company_ticker
    - company_name         <- companies.company_name
    - company_is_delisted  <- companies.company_is_delisted
    - exchange_name        <- exchanges.exchange_name
    - industry_name        <- industries.industry_name
    - industry_sector      <- industries.industry_sector
    - sic_industries       <- sicindustries.sic_industry
    """

    db_base = _build_hdfs_path("db")

    companies_path = f"{db_base}/companies_*.parquet"
    exchanges_path = f"{db_base}/exchanges_*.parquet"
    industries_path = f"{db_base}/industries_*.parquet"
    sic_path = f"{db_base}/sicindustries_*.parquet"

    print(f"[DIM_COMPANY] Reading companies from: {companies_path}")
    companies_df = spark.read.parquet(companies_path)

    print(f"[DIM_COMPANY] Reading exchanges from: {exchanges_path}")
    exchanges_df = spark.read.parquet(exchanges_path)

    print(f"[DIM_COMPANY] Reading industries from: {industries_path}")
    industries_df = spark.read.parquet(industries_path)

    print(f"[DIM_COMPANY] Reading sicindustries from: {sic_path}")
    sic_df = spark.read.parquet(sic_path)

    # Basic schema checks
    comp_expected = {
        "company_id",
        "company_exchange_id",
        "company_industry_id",
        "company_sic_id",
        "company_name",
        "company_ticker",
        "company_is_delisted",
    }
    exch_expected = {"exchange_id", "exchange_name"}
    ind_expected = {"industry_id", "industry_name", "industry_sector"}
    sic_expected = {"sic_id", "sic_industry"}

    missing_comp = sorted(comp_expected - set(companies_df.columns))
    missing_exch = sorted(exch_expected - set(exchanges_df.columns))
    missing_ind = sorted(ind_expected - set(industries_df.columns))
    missing_sic = sorted(sic_expected - set(sic_df.columns))

    errors = []
    if missing_comp:
        errors.append(f"companies missing: {missing_comp}")
    if missing_exch:
        errors.append(f"exchanges missing: {missing_exch}")
    if missing_ind:
        errors.append(f"industries missing: {missing_ind}")
    if missing_sic:
        errors.append(f"sicindustries missing: {missing_sic}")
    if errors:
        raise ValueError(
            "Schema mismatch for DIM_COMPANY sources -> " + "; ".join(errors)
        )

    dim_company_df = (
        companies_df.alias("c")
        .join(
            exchanges_df.alias("e"),
            F.col("c.company_exchange_id") == F.col("e.exchange_id"),
            "left",
        )
        .join(
            industries_df.alias("i"),
            F.col("c.company_industry_id") == F.col("i.industry_id"),
            "left",
        )
        .join(
            sic_df.alias("s"),
            F.col("c.company_sic_id") == F.col("s.sic_id"),
            "left",
        )
        .select(
            F.col("c.company_id").cast("int").alias("company_key"),
            F.col("c.company_ticker").alias("company_ticker"),
            F.col("c.company_name"),
            F.col("c.company_is_delisted").cast("boolean"),
            F.col("e.exchange_name").alias("exchange_name"),
            F.col("i.industry_name").alias("industry_name"),
            F.col("i.industry_sector").alias("industry_sector"),
            F.col("s.sic_industry").alias("sic_industries"),
        )
        .dropDuplicates(["company_key"])
    )

    pdf = dim_company_df.toPandas()
    if pdf.empty:
        print("[DIM_COMPANY] No company records found; skipping.")
        return

    print(f"[DIM_COMPANY] Loading {len(pdf)} rows into DuckDB")
    con.register("df_dim_company", pdf)
    con.execute(
        """
		INSERT OR REPLACE INTO dim_company (
			company_key,
			company_ticker,
			company_name,
			company_is_delisted,
			exchange_name,
			industry_name,
			industry_sector,
			sic_industries
		)
		SELECT
			company_key,
			company_ticker,
			company_name,
			company_is_delisted,
			exchange_name,
			industry_name,
			industry_sector,
			sic_industries
		FROM df_dim_company
		"""
    )
    con.unregister("df_dim_company")


def main() -> None:
    _require_hdfs_config()

    DUCKDB_PATH.parent.mkdir(parents=True, exist_ok=True)
    print("DuckDB file:", DUCKDB_PATH)

    spark = _get_spark_session()
    try:
        con = duckdb.connect(str(DUCKDB_PATH))
        try:
            con.execute("SET schema 'data_warehouse'")
            # Tables dim_date and dim_company must already exist in DuckDB.
            # This ETL step only inserts/refreshes data.
            _build_dim_date(spark, con)
            _build_dim_company(spark, con)
        finally:
            con.close()
    finally:
        spark.stop()

    print("[DIM_DATE], [DIM_COMPANY] have been (re)built in DuckDB.")


if __name__ == "__main__":
    main()
