import os
import json
import datetime
import pandas as pd


def get_latest_file_in_directory(directory, extension):
    """
    Get the latest file in a directory with a specific extension.

    :param directory: Directory to search for files.
    :param extension: File extension to look for.
    :return: Path to the latest file or None if no files are found.
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


def convert_ohlcs_to_parquet():
    """Convert OHLC JSON data to Parquet format."""
    # Define paths
    base_dir = os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    )
    raw_dir = os.path.join(base_dir, "data", "raw", "ohlcs")
    output_dir = os.path.join(base_dir, "data", "completed", "ohlcs_to_dl")

    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)

    # Get latest raw OHLC file
    latest_file = get_latest_file_in_directory(raw_dir, ".json")
    if not latest_file:
        print("No raw OHLC file found.")
        return None

    print(f"\nProcessing OHLC file: {latest_file}")

    # Load JSON data
    with open(latest_file, "r", encoding="utf-8") as f:
        ohlc_data = json.load(f)

    print(f"Loaded {len(ohlc_data)} OHLC records")

    # Rename columns to be more descriptive
    processed_ohlcs = []
    for record in ohlc_data:
        processed_record = {
            "ticker": record.get("T"),
            "volume": record.get("v"),
            "vwap": record.get("vw"),  # Volume Weighted Average Price
            "open": record.get("o"),
            "close": record.get("c"),
            "high": record.get("h"),
            "low": record.get("l"),
            "timestamp": record.get("t"),  # Unix timestamp in milliseconds
            "transactions": record.get("n"),  # Number of transactions
        }
        processed_ohlcs.append(processed_record)

    # Convert to DataFrame
    df = pd.DataFrame(processed_ohlcs)

    # Convert timestamp from milliseconds to datetime
    if "timestamp" in df.columns:
        df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")

    # Generate output filename with timestamp
    timestamp = datetime.datetime.now().strftime("%Y_%m_%d")
    output_file = os.path.join(output_dir, f"ohlcs_parquet_{timestamp}.parquet")

    # Save as Parquet
    df.to_parquet(output_file, engine="pyarrow", compression="snappy", index=False)

    print(f"Converted {len(df)} OHLC records to Parquet")
    print(f"Saved to: {output_file}")
    print(f"File size: {os.path.getsize(output_file) / (1024 * 1024):.2f} MB")

    return output_file


def main():
    """Convert news and OHLC JSON data to Parquet."""
    print("=" * 60)
    print("Converting JSON to Parquet Format")
    print("=" * 60)

    try:
        ohlc_file = convert_ohlcs_to_parquet()

        print("\n" + "=" * 60)
        print("Conversion completed successfully !")
        print("=" * 60)

        if ohlc_file:
            print(f"OHLC: {ohlc_file}")

    except Exception as e:
        print(f"\nError: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
