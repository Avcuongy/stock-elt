import os
import sys
import datetime
import pandas as pd
from sqlalchemy import create_engine
from utils.config_env import DATABASE_URL

DATABASE_URL = DATABASE_URL


def get_db_connection():
    """
    Create database connection.
    Update the connection string with your MySQL credentials.
    """
    # Connection string database url
    connection_string = DATABASE_URL
    if not connection_string:
        raise ValueError("DATABASE_URL is not set")

    engine = create_engine(connection_string, echo=False)
    return engine


def export_to_parquet():
    """Export toàn bộ các bảng backend (regions, exchanges, industries,
    sicindustries, companies) trong database sang các file Parquet full-load.

    Each table will be exported to a separate Parquet file named like
    {table_name}_{timestamp}.parquet, stored in data/completed/db_to_dl
    """

    # Define paths
    base_dir = os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    )
    output_dir = os.path.join(base_dir, "data", "completed", "db_to_dl")

    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)

    print("=" * 60)
    print("Exporting MySQL backend tables to Parquet")
    print("Output directory:", output_dir)
    print("=" * 60)

    tables = [
        "regions",
        "exchanges",
        "industries",
        "sicindustries",
        "companies",
    ]

    # Use current date for timestamping files
    timestamp = datetime.datetime.now().strftime("%Y_%m_%d")

    try:
        # Get database connection
        engine = get_db_connection()

        exported_files = {}

        for table in tables:
            print("\n" + "-" * 60)
            print(f"Exporting table: {table}")

            query = f"SELECT * FROM {table}"
            df = pd.read_sql(query, engine)

            if df.empty:
                print(
                    f"Warning: Table '{table}' returned no data. Skipping Parquet file."
                )
                continue

            output_file = os.path.join(output_dir, f"{table}_{timestamp}.parquet")

            # Save as Parquet (full dump per table)
            df.to_parquet(
                output_file,
                engine="pyarrow",
                compression="snappy",
                index=False,
            )

            print(f"Rows exported   : {len(df):,}")
            print(f"Columns         : {list(df.columns)}")
            print(f"Saved to        : {output_file}")
            print(
                f"File size (MB)  : {os.path.getsize(output_file) / (1024 * 1024):.2f}"
            )

            exported_files[table] = output_file

        print("\n" + "=" * 60)
        print("Export Completed")
        print("Tables exported:")
        for tbl, path in exported_files.items():
            print(f"  - {tbl}: {path}")

        if not exported_files:
            print("No tables were exported (all empty or errors).")

        return exported_files

    except Exception as e:
        print(f"\nError while exporting tables to Parquet: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


def main():
    """
    Main function.
    """
    export_to_parquet()


if __name__ == "__main__":
    main()
