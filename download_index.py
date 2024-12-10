# A script to download data from the xeno-canto API.
# Run this with:
#   uv run download_index.py

import requests
import time
import csv
from pathlib import Path


def get_index_one_page(page):
    """
    Query the xeno-canto API for crow sounds.

    Args:
        page (int): The page number to fetch (default: 1)
    Returns:
        list: A list of tuples containing (id, species, url) for each recording
    """
    base_url = "https://xeno-canto.org/api/2/recordings"
    params = {
        "query": "gen:corvus",  # Genus Corvus (crows)
        "page": page,
    }

    try:
        response = requests.get(base_url, params=params)
        response.raise_for_status()
        data = response.json()

        return [
            (
                recording["id"],
                f"{recording['gen']} {recording['sp']}",
                recording["file"],
            )
            for recording in data["recordings"]
        ]

    except requests.exceptions.RequestException as e:
        print(f"Error fetching data: {e}")
        return []


def get_index():
    """
    Query the xeno-canto API for all crow sounds and save to CSV.
    Creates a data directory if it doesn't exist.

    Returns:
        list: A list of tuples containing (id, species, url) for all recordings
    """
    Path("data").mkdir(exist_ok=True)

    all_recordings = []
    page = 1

    while True:
        recordings = get_index_one_page(page)
        if not recordings:  # Stop if we get an empty page
            break

        all_recordings.extend(recordings)
        print(f"Found {len(all_recordings)} recordings after fetching page {page}")

        # Make a test request to get total pages
        if page == 1:
            response = requests.get(
                "https://xeno-canto.org/api/2/recordings",
                params={"query": "gen:corvus", "page": 1},
            )
            if response.ok:
                num_pages = response.json()["numPages"]
                print(f"Total pages to fetch: {num_pages}")
                if page >= num_pages:
                    break

        time.sleep(1)  # Wait before next request
        page += 1

    print(f"\nDownload complete. Total recordings found: {len(all_recordings)}")

    # Save to CSV
    with open("data/index.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["id", "species", "url"])  # header
        writer.writerows(all_recordings)

    return all_recordings


if __name__ == "__main__":
    get_index()
