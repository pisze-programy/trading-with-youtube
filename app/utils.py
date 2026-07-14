import os
import csv
from typing import Dict, List, Any
from fastapi.exceptions import HTTPException
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.formatters import TextFormatter
import requests
from dotenv import load_dotenv

load_dotenv()


def get_video_id(url: str) -> str:
    return url.split("=")[-1]


def fetch_transcript_with_timestamps(url: str) -> List[Dict[str, Any]]:
    try:
        vid = get_video_id(url)
        raw = YouTubeTranscriptApi.get_transcript(vid, languages=["en", "pl"])
        transcript_data = []
        for item in raw:
            transcript_data.append({
                "start": item["start"],
                "duration": item["duration"],
                "text": item["text"]
            })
        return transcript_data
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


def analyze_with_ollama(transcript: List[Dict[str, Any]], prompt_template: str) -> Dict[str, Any]:
    try:
        transcript_text = " ".join([item["text"] for item in transcript])
        full_prompt = prompt_template.format(transcript=transcript_text)

        
        response = requests.post(
            os.getenv("OLLAMA_API_URL"),
            json={
                "model": os.getenv("OLLAMA_MODEL", "llama3"),
                "prompt": full_prompt,
                "stream": False
            },
            timeout=60
        )
        
        if response.status_code == 200:
            return {
                "analysis": response.json().get("response", ""),
                "transcript": transcript 
            }
        else:
            raise HTTPException(status_code=500, detail="Ollama analysis failed")
            
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Analysis error: {str(exc)}") from exc


def save_to_csv(data: Dict[str, Any], filename: str = "analysis_results.csv") -> None:
    if not os.path.exists(os.getenv("DATA_DIR", "data")):
        os.makedirs(os.getenv("DATA_DIR", "data"))
        
    filepath = os.path.join(os.getenv("DATA_DIR", "data"), filename)
    
    csv_data = []
    for key, value in data.items():
        if key == "transcript":
            continue
        csv_data.append({"key": key, "value": str(value)})
    
    with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['key', 'value']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(csv_data)


def fetch_and_analyze(url: str, prompt_template: str) -> Dict[str, Any]:
    transcript = fetch_transcript_with_timestamps(url)
    analysis = analyze_with_ollama(transcript, prompt_template)
    return analysis