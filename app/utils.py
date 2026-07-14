import csv
import json
import os
import requests
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


def fetch_transcript_with_timestamps(url: str) -> List[Dict[str, Any]]:
    vid = get_video_id(url)
    try:
        raw = YouTubeTranscriptApi(

        ).fetch(vid, languages=['en', 'pl'], preserve_formatting=True)
        return " ".join([w.text for w in raw])
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


def analyze_with_ollama(transcript: List[Dict[str, Any]]) -> Dict[str, Any]:
    prompt_template = ""
    with open("prompts/youtube.md", "r", encoding="utf-8") as f:
        prompt_template = f.read()

    if not prompt_template or not transcript:
        return ""

    try:
        full_prompt = prompt_template.replace("{transcript}", transcript)

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


def save_to_csv(data: str, filename: str = "analysis_results.csv") -> None:
    data_dir = os.getenv("DATA_DIR")
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
        
    filepath = os.path.join(data_dir, filename)

    csv_data = [data]

    with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['value']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(csv_data)


def fetch_and_analyze(url: str, filename: str = "analysis_results.csv") -> Dict[str, Any]:
    transcript = fetch_transcript_with_timestamps(url)
    analysis = analyze_with_ollama(transcript)
    save_to_csv(analysis, filename=filename)
    return analysis