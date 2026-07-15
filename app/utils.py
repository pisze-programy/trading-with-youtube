import json
import os
import re
import requests
import yt_dlp
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
from fastapi.exceptions import HTTPException
from typing import Dict, List, Any
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.formatters import TextFormatter
from youtube_transcript_api.proxies import WebshareProxyConfig

load_dotenv()

PROXY_USERNAME = os.getenv("PROXY_USERNAME")
PROXY_PASSWORD = os.getenv("PROXY_PASSWORD")

def get_video_id(url: str) -> str:
    return url.split("=")[-1]


def fetch_transcript(url: str) -> List[Dict[str, Any]]:
    vid = get_video_id(url)
    try:
        raw = YouTubeTranscriptApi(
            proxy_config=WebshareProxyConfig(
                proxy_username=f"{PROXY_USERNAME}",
                proxy_password=f"{PROXY_PASSWORD}",
            )
        ).fetch(vid, languages=['en', 'pl'], preserve_formatting=True)
        return " ".join([w.text for w in raw])
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


def analyze_with_ollama(meta: Dict[str, Any], transcript: List[Dict[str, Any]]) -> Dict[str, Any]:
    prompt = ""

    with open("prompts/youtube.md", "r", encoding="utf-8") as f:
        prompt = f.read()

    if not prompt or not transcript:
        return ""

    try:
        prompt = prompt.replace("{TRANSCRIPT}", str(transcript))
        prompt = prompt.replace("{CHANNEL_NAME}", str(meta.get("channel_name", "N/A")))
        prompt = prompt.replace("{VIDEO_TITLE}", str(meta.get("title", "N/A")))
        prompt = prompt.replace("{VIDEO_URL}", str(meta.get("url", "N/A")))
        prompt = prompt.replace("{PUBLISHED_AT}", str(meta.get("published_at", "N/A")))

        response = requests.post(
            os.getenv("OLLAMA_API_URL"),
            json={
                "model": os.getenv("OLLAMA_MODEL"),
                "prompt": prompt,
                "stream": False
            },
            timeout=60
        )
        
        if response.status_code == 200:
            raw_content = response.json().get("response", "")
            try:
                data = json.loads(raw_content)
            except json.JSONDecodeError:
                if isinstance(raw_content, list):
                    raw_content = raw_content[0]
                data = json.loads(raw_content)
            if isinstance(data, str):
                data = json.loads(data)

            return data
        else:
            raise HTTPException(status_code=500, detail="Ollama analysis failed")
            
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Analysis error: {str(exc)}") from exc


def fetch_video_metadata(ydl, url: str) -> Dict[str, Any]:
    info = ydl.extract_info(url, download=False)
    # upload_date '20260712'
    raw_date = info.get("upload_date")
    # formatted '2026-07-12'
    if raw_date and len(raw_date) == 8:
        formatted_date = datetime.strptime(raw_date, "%Y%m%d").strftime("%Y-%m-%d")
    else:
        formatted_date = raw_date

    return {
        "title": info.get("title"),
        "channel_name": info.get("uploader"),
        "published_at": formatted_date,
        "upload_date": raw_date,
        "channel_id": info.get("channel_id"),
        "url": info.get("webpage_url"),
        "duration": info.get("duration")
    }


def sanitize_filename(name: str) -> str:
    name = name.replace(" ", "_")
    name = re.sub(r'(?u)[^-\w]', '', name)
    return name


def save_to_file(meta: Dict[str, Any], data: Dict[str, Any]):
    data_dir = os.getenv("DATA_DIR")

    if not os.path.exists(data_dir):
        os.makedirs(data_dir)

    raw_channel_name = meta.get("channel_name", "unknown")
    filename = f"{sanitize_filename(raw_channel_name)}.json"
    filepath = os.path.join(data_dir, filename)

    try:
        if os.path.exists(filepath):
            with open(filepath, 'r', encoding='utf-8') as fp:
                existing = json.load(fp)
                if not isinstance(existing, list):
                    existing = []
        else:
            existing = []
    except Exception:
        existing = []
    
    existing.append(data)

    with open(filepath, 'w', encoding='utf-8') as fp:
        json.dump(existing, fp, indent=2, ensure_ascii=False)


def get_channel_videos(ydl, channel_url):
    info = ydl.extract_info(channel_url, download=False)
    print(json.dumps(ydl.sanitize_info(info)))

    return [entry.get('id') for entry in info.get('entries', []) if entry]


def fetch_and_analyze(channel_name: str) -> Dict[str, Any]:
    channel_url = f"https://www.youtube.com/{channel_name}/videos"

    threshold_date = datetime(2025, 1, 1, tzinfo=timezone.utc)
    ydl_opts = {
        'quiet': True,
        'extract_flat': True,
        'skip_download': True,
        'no_warnings': True,
        'ignoreerrors': True,
        'writesubtitles': False,
        'writeautomaticsub': False,
        'playlistend': 50,
        'postprocessors': [],
        'proxy': f'http://mdtduclo-rotate:1mhd0l5qhowm@p.webshare.io:80'
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        # fetch all channel videos
        video_ids = get_channel_videos(ydl, channel_url)

        for vid in video_ids:
            url = f"https://www.youtube.com/watch?v={vid}"
            meta = fetch_video_metadata(ydl, url)
            raw_date = meta.get('upload_date')

            if not raw_date: continue
            upload_date = datetime.strptime(raw_date, '%Y%m%d').replace(tzinfo=timezone.utc)
            if upload_date < threshold_date:
                continue

            try:
                transcript = fetch_transcript(url)
                analysis = analyze_with_ollama(meta, transcript)
                save_to_file(meta, analysis)
            except Exception as e:
                print(f"Failed to process {vid}: {e}")
    return None