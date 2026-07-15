import csv
import json
import os
import requests
import yt_dlp
from datetime import datetime, timedelta
from pathlib import Path

# TODO: ENVS?
BASE_DIR = Path(__file__).resolve().parent.parent
CSV_PATH = BASE_DIR / 'collections' / 'youtube.csv'
API_URL = "http://localhost:8000/analyze_channel"

def process():
    rows = []
    with open(CSV_PATH, mode='r', newline='') as f:
        rows = list(csv.DictReader(f))

    for row in rows:
        channel_name = row['channel']

        try:
            resp = requests.post(API_URL, json={"channel_name": channel_name})

            resp.raise_for_status()
            print(f"Success: {channel_name}")
        except Exception as e:
            print(f"Error {channel_name}: {e}")


if __name__ == "__main__":
    process()