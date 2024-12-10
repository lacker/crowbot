# Run this with:
#   uv run download_files.py

import requests
from pathlib import Path
import csv
import time


def download_recording(recording_id: str, url: str) -> bool:
    """
    Download a single xeno-canto recording and save it as MP3.
    """
    output_path = f"data/{recording_id}.mp3"

    # Skip if file already exists
    if Path(output_path).exists():
        print(f"Skipping {recording_id}, already downloaded")
        return False

    try:
        response = requests.get(url, allow_redirects=True)
        response.raise_for_status()

        # Write the MP3 content to file
        with open(output_path, "wb") as f:
            f.write(response.content)

        print(f"Successfully downloaded {recording_id}")
        return True

    except requests.exceptions.RequestException as e:
        print(f"Error downloading {recording_id}: {e}")
        return False


def download_all():
    """
    Download all recordings listed in data/index.csv.
    Waits 1 second between downloads to be nice to the server.
    """
    if not Path("data/index.csv").exists():
        print("Error: data/index.csv not found")
        return

    downloaded_count = 0

    with open("data/index.csv", "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        total_files = sum(1 for _ in reader)  # Count total files
        f.seek(0)  # Reset file pointer
        next(reader)  # Skip header row

        for i, row in enumerate(reader, 1):
            if download_recording(row["id"], row["url"]):
                downloaded_count += 1
                print(
                    f"Progress: {i}/{total_files} files processed, {downloaded_count} new downloads"
                )
                if i < total_files:  # Don't sleep after the last file
                    time.sleep(1)
            else:
                print(
                    f"Progress: {i}/{total_files} files processed, {downloaded_count} new downloads"
                )

    print(f"\nDownload complete! Downloaded {downloaded_count} new files")


if __name__ == "__main__":
    download_all()
