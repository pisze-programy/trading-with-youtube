import os
import json
from typing import Dict, List, Any
from fastapi.exceptions import HTTPException
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.formatters import TextFormatter
import requests
from dotenv import load_dotenv

load_dotenv()


PROXY_USERNAME = os.getenv("PROXY_USERNAME")
PROXY_PASSWORD = os.getenv("PROXY_PASSWORD")

def get_video_id(url: str) -> str:
    return url.split("=")[-1]


def fetch_transcript_with_timestamps(url: str) -> List[Dict[str, Any]]:
    vid = get_video_id(url)
    try:
        raw = YouTubeTranscriptApi(
            proxy_config=WebshareProxyConfig(
                proxy_username=PROXY_USERNAME,
                proxy_password=PROXY_PASSWORD,
            )
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
    if not os.path.exists(os.getenv("DATA_DIR")):
        os.makedirs(os.getenv("DATA_DIR"))
        
    filepath = os.path.join(os.getenv("DATA_DIR"), filename)
    
    csv_data.append(data)
    
    with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['value']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(csv_data)


def fetch_and_analyze(url: str, filename: str = "analysis_results.csv") -> Dict[str, Any]:
    transcript = fetch_transcript_with_timestamps(url)
    analysis = analyze_with_ollama(transcript)
    utils.save_to_csv(analysis, filename=filename)
    return analysis