
import json
import os
import requests
import yt_dlp
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

        ).fetch(vid, languages=['en', 'pl'], preserve_formatting=True)
        return " ".join([w.text for w in raw])
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


def analyze_with_ollama(meta: Dict[str, Any], transcript: List[Dict[str, Any]]) -> Dict[str, Any]:
    prompt_template = ""

    with open("prompts/youtube.md", "r", encoding="utf-8") as f:
        prompt_template = f.read()

    if not prompt_template or not transcript:
        return ""

    try:
        full_prompt = prompt_template.format(
            TRANSCRIPT=transcript,
            CHANNEL_NAME=meta.get("channel_name") or "unknown",
            VIDEO_TITLE=meta.get("title") or "unknown",
            VIDEO_URL=meta.get("url") or "unknown",
            PUBLISHED_AT=meta.get("published_at") or "unknown"
        )

        response = requests.post(
            os.getenv("OLLAMA_API_URL"),
            json={
                "model": os.getenv("OLLAMA_MODEL"),
                "prompt": full_prompt,
                "stream": False
            },
            timeout=60
        )
        
        if response.status_code == 200:
            return response.json().get("response", "")
        else:
            raise HTTPException(status_code=500, detail="Ollama analysis failed")
            
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Analysis error: {str(exc)}") from exc


def fetch_video_metadata(url: str) -> Dict[str, Any]:
    ydl_opts = {
        'skip_download': True,
        'quiet': True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        return {
            "title": info.get("title"),
            "channel_name": info.get("uploader"),
            "published_at": info.get("upload_date"),
            "channel_id": info.get("channel_id"),
            "url": info.get("webpage_url"),
            "duration": info.get("duration")
        }
    return None


def save_to_file(meta: Dict[str, Any], data: Any):
    data_dir = os.getenv("DATA_DIR")

    if not os.path.exists(data_dir):
        os.makedirs(data_dir)

    filename = f"{meta.get('channel_name', 'unknown')}.json"
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


def fetch_and_analyze(url: str) -> Dict[str, Any]:
    transcript = fetch_transcript(url)
    meta = fetch_video_metadata(url)
    analysis_text = analyze_with_ollama(meta, transcript)
    save_to_file(meta, analysis_text)
    return analysis_text