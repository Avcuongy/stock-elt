import os
import json
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.exc import IntegrityError
from utils.config_env import DATABASE_URL


def get_latest_file_in_directory(directory, extension):
    """
    Get the latest file in a directory with a specific extension.
    """
    files = [
        os.path.join(directory, f)
        for f in os.listdir(directory)
        if f.endswith(extension)
    ]
    if not files:
        return None
    latest_file = max(files, key=os.path.getmtime)
    return latest_file


def get_db_connection():
    """
    Create database connection.
    Update the connection string with your MySQL credentials.
    """
    database_url = DATABASE_URL
    if not database_url:
        raise ValueError("DATABASE_URL is not set")

    engine = create_engine(database_url, echo=False)
    return engine


def load_exchanges(engine):
    """
    Load exchanges data into MySQL.
    """
    # Define paths
    base_dir = os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    )
    processed_dir = os.path.join(base_dir, "data", "processed", "exchanges")

    # Get latest file
    latest_file = get_latest_file_in_directory(processed_dir, ".json")
    if not latest_file:
        print("No processed exchanges file found.")
        return

    print(f"\nLoading exchanges from: {latest_file}")

    # Load JSON data
    with open(latest_file, "r", encoding="utf-8") as f:
        exchanges_data = json.load(f)

    # Insert into database
    inserted = 0
    skipped = 0
    errors = 0

    with engine.connect() as conn:
        for exchange in exchanges_data:
            try:
                exchange_name = exchange.get("name")
                region_name = exchange.get("region")

                if not exchange_name:
                    print(f"Skipping exchange with no name: {exchange}")
                    skipped += 1
                    continue

                # Get region_id from region name
                region_query = text(
                    """
                    SELECT region_id FROM regions WHERE region_name = :region_name
                """
                )
                result = conn.execute(region_query, {"region_name": region_name})
                region_row = result.fetchone()

                if not region_row:
                    print(
                        f"Warning: Region '{region_name}' not found for exchange '{exchange_name}'. Skipping."
                    )
                    errors += 1
                    continue

                region_id = region_row[0]

                # Insert exchange
                sql = text(
                    """
                    INSERT INTO exchanges (exchange_name, exchange_region_id)
                    VALUES (:name, :region_id)
                    ON DUPLICATE KEY UPDATE
                        exchange_region_id = :region_id
                """
                )

                conn.execute(sql, {"name": exchange_name, "region_id": region_id})
                conn.commit()
                inserted += 1

            except IntegrityError as e:
                skipped += 1
                print(f"Skipped exchange {exchange.get('name')}: {e}")
            except Exception as e:
                errors += 1
                print(f"Error inserting exchange {exchange.get('name')}: {e}")

    print(f"Exchanges: {inserted} inserted/updated, {skipped} skipped, {errors} errors")


def main():
    """
    Main function to load exchanges table.
    """
    print("=" * 60)
    print("Loading Exchanges to MySQL")
    print("=" * 60)

    try:
        # Get database connection
        engine = get_db_connection()

        # Load exchanges
        load_exchanges(engine)

        print("\n" + "=" * 60)
        print("Load completed successfully!")
        print("=" * 60)

    except Exception as e:
        print(f"\nError: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
