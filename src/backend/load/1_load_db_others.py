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


def load_regions(engine):
    """
    Load regions data into MySQL.
    """
    # Define paths
    base_dir = os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    )
    processed_dir = os.path.join(base_dir, "data", "processed", "regions")

    # Get latest file
    latest_file = get_latest_file_in_directory(processed_dir, ".json")
    if not latest_file:
        print("No processed regions file found.")
        return

    print(f"\nLoading regions from: {latest_file}")

    # Load JSON data
    with open(latest_file, "r", encoding="utf-8") as f:
        regions_data = json.load(f)

    # Insert into database
    inserted = 0
    skipped = 0

    with engine.connect() as conn:
        for region in regions_data:
            try:
                # Parse time strings
                local_open = region.get("local_open", "00:00")
                local_close = region.get("local_close", "00:00")

                sql = text(
                    """
                    INSERT INTO regions (region_name, region_local_open, region_local_close)
                    VALUES (:name, :open, :close)
                    ON DUPLICATE KEY UPDATE
                        region_local_open = :open,
                        region_local_close = :close
                """
                )

                conn.execute(
                    sql,
                    {
                        "name": region.get("region"),
                        "open": local_open,
                        "close": local_close,
                    },
                )
                conn.commit()
                inserted += 1

            except IntegrityError as e:
                skipped += 1
                print(f"Skipped region {region.get('region')}: {e}")
            except Exception as e:
                print(f"Error inserting region {region.get('region')}: {e}")

    print(f"Regions: {inserted} inserted/updated, {skipped} skipped")


def load_industries(engine):
    """
    Load industries data into MySQL.
    """
    # Define paths
    base_dir = os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    )
    processed_dir = os.path.join(base_dir, "data", "processed", "industries")

    # Get latest file
    latest_file = get_latest_file_in_directory(processed_dir, ".json")
    if not latest_file:
        print("No processed industries file found.")
        return

    print(f"\nLoading industries from: {latest_file}")

    # Load JSON data
    with open(latest_file, "r", encoding="utf-8") as f:
        industries_data = json.load(f)

    # Insert into database
    inserted = 0
    skipped = 0

    with engine.connect() as conn:
        for industry in industries_data:
            try:
                sql = text(
                    """
                    INSERT INTO industries (industry_name, industry_sector)
                    VALUES (:name, :sector)
                    ON DUPLICATE KEY UPDATE
                        industry_sector = :sector
                """
                )

                conn.execute(
                    sql,
                    {
                        "name": industry.get("industry"),
                        "sector": industry.get("sector"),
                    },
                )
                conn.commit()
                inserted += 1

            except IntegrityError as e:
                skipped += 1
                print(f"Skipped industry {industry.get('industry')}: {e}")
            except Exception as e:
                print(f"Error inserting industry {industry.get('industry')}: {e}")

    print(f"Industries: {inserted} inserted/updated, {skipped} skipped")


def load_sicindustries(engine):
    """
    Load SIC industries data into MySQL.
    """
    # Define paths
    base_dir = os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    )
    processed_dir = os.path.join(base_dir, "data", "processed", "sicindustries")

    # Get latest file
    latest_file = get_latest_file_in_directory(processed_dir, ".json")
    if not latest_file:
        print("No processed sicindustries file found.")
        return

    print(f"\nLoading SIC industries from: {latest_file}")

    # Load JSON data
    with open(latest_file, "r", encoding="utf-8") as f:
        sic_data = json.load(f)

    # Insert into database
    inserted = 0
    skipped = 0

    with engine.connect() as conn:
        for sic in sic_data:
            try:
                sic_id = sic.get("sic")
                if not sic_id:
                    continue

                sql = text(
                    """
                    INSERT INTO sicindustries (sic_id, sic_industry, sic_sector)
                    VALUES (:sic_id, :industry, :sector)
                    ON DUPLICATE KEY UPDATE
                        sic_industry = :industry,
                        sic_sector = :sector
                """
                )

                conn.execute(
                    sql,
                    {
                        "sic_id": int(sic_id),
                        "industry": sic.get("sicIndustry"),
                        "sector": sic.get("sicSector"),
                    },
                )
                conn.commit()
                inserted += 1

            except IntegrityError as e:
                skipped += 1
                print(f"Skipped SIC {sic.get('sic')}: {e}")
            except Exception as e:
                print(f"Error inserting SIC {sic.get('sic')}: {e}")

    print(f"SIC Industries: {inserted} inserted/updated, {skipped} skipped")


def main():
    """
    Main function to load all dimension tables.
    """
    print("=" * 60)
    print("Loading Regions + Industries + SIC Industries to MySQL")
    print("=" * 60)

    try:
        # Get database connection
        engine = get_db_connection()

        # Load tables in order (no dependencies)
        load_regions(engine)
        load_industries(engine)
        load_sicindustries(engine)

        print("\n" + "=" * 60)
        print("Load completed successfully!")
        print("=" * 60)

    except Exception as e:
        print(f"\nError: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
