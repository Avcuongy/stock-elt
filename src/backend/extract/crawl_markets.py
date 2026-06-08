import requests
import json
import datetime
import os
from utils.config_env import ALPHAVANTAGE_API_KEY

# Alpha Vantage API Configuration
API_KEY = ALPHAVANTAGE_API_KEY
FUNCTION = "MARKET_STATUS"


# Crawl market status data from Alpha Vantage API
def crawl_markets():
    """
    Crawl market status data from Alpha Vantage API.
    Saves data to ./data/raw/markets/crawl_markets_{date}.json
    """
    # Construct the API URL
    url = f"https://www.alphavantage.co/query?function={FUNCTION}&apikey={API_KEY}"

    # Make a GET request to the API
    response = requests.get(url)
    data = response.json().get("markets", [])

    # Serialize to JSON
    json_payload = json.dumps(data, indent=4)

    # Get yesterday's date
    yesterday = datetime.date.today() - datetime.timedelta(days=1)
    date_str = yesterday.strftime("%Y_%m_%d")

    # Create directory if it doesn't exist
    os.makedirs("./data/raw/markets", exist_ok=True)

    # Define the file path
    path = f"./data/raw/markets/crawl_markets_{date_str}.json"

    # Write the JSON data to a file
    with open(path, "w") as outfile:
        outfile.write(json_payload)

    print(f"Successfully saved {len(data)} regions and exchanges to {path}")
    return path


if __name__ == "__main__":
    crawl_markets()
