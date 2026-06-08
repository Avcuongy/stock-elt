import requests
import json
import datetime
import os
from utils.config_env import SEC_API_KEY

# SEC API Configuration
SEC_API_KEY = SEC_API_KEY
# List of stock EXCHANGES to extract data from
EXCHANGES = ["nasdaq", "nyse"]

# Maximum number of companies to keep.
COMPANY_LIMIT = 1000  # Extract all companies (set to 0 for no limit)


# Crawl company data from SEC API
def crawl_companies():
    """
    Crawl company data from SEC API for NYSE and NASDAQ.
    Saves data to ./data/raw/companies/crawl_companies_{date}.json
    """

    # Initialize an empty list to hold company data
    list_companies = []

    # Fetch company mappings from all EXCHANGES
    for exchange in EXCHANGES:
        url = f"https://api.sec-api.io/mapping/exchange/{exchange}?token={SEC_API_KEY}"
        response = requests.get(url)
        data = response.json()
        list_companies.extend(data)
        print(
            f"Extracted {len(data)} companies from the {exchange.upper()} stock exchange."
        )

    # Apply LIMIT if configured (0 = no limit)
    if COMPANY_LIMIT and COMPANY_LIMIT > 0:
        list_companies = list_companies[:COMPANY_LIMIT]
        print(f"Applying limit: keeping first {len(list_companies)} companies (COMPANY_LIMIT={COMPANY_LIMIT}).")

    # Serialize to JSON
    json_payload = json.dumps(list_companies, indent=4)

    # Get yesterday's date
    yesterday = datetime.date.today() - datetime.timedelta(days=1)
    date_str = yesterday.strftime("%Y_%m_%d")

    # Create directory if it doesn't exist
    os.makedirs("./data/raw/companies", exist_ok=True)

    # Define the file path
    path = f"./data/raw/companies/crawl_companies_{date_str}.json"

    # Write the JSON data to a file
    with open(path, "w") as outfile:
        outfile.write(json_payload)

    print(f"Successfully saved {len(list_companies)} companies to {path}")
    return path


if __name__ == "__main__":
    crawl_companies()
