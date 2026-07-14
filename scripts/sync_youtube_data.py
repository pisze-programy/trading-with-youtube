import csv
import requests
import yt_dlp
import os
from pathlib import Path

# ENVS?
BASE_DIR = Path(__file__).resolve().parent.parent
CSV_PATH = BASE_DIR / 'collections' / 'youtube.csv'
API_URL = "http://localhost:8000/analyze_video"


def get_channel_videos(channel_url):
    ydl_opts = {'quiet': True, 'extract_flat': True}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(channel_url, download=False)
        return [entry['id'] for entry in info['entries']]


def process():
    rows = []
    with open(CSV_PATH, mode='r', newline='') as f:
        rows = list(csv.DictReader(f))

    for row in rows:
        channel_handle = row['channel']
        last_id = row['lastSeenVideoId']
        channel_url = f"https://www.youtube.com/{channel_handle}/videos"

        print(f"Checking: {channel_handle}")
        video_ids = get_channel_videos(channel_url)

        if last_id in video_ids:
            idx = video_ids.index(last_id)
            new_videos = video_ids[:idx]
        else:
            new_videos = video_ids

        for vid in reversed(new_videos):
            url = f"https://www.youtube.com/watch?v={vid}"
            try:
                resp = requests.post(API_URL, json={"url": url})
                if resp.status_code == 200:
                    row['lastSeenVideoId'] = vid
                    print(f"Success: {vid}")

                    with open(CSV_PATH, mode='w', newline='') as f:
                        writer = csv.DictWriter(f, fieldnames=['channel', 'lastSeenVideoId'])
                        writer.writeheader()
                        writer.writerows(rows)
            except Exception as e:
                print(f"Error {vid}: {e}")


if __name__ == "__main__":
    process()