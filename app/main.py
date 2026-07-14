from fastapi import FastAPI
import app.utils as utils
from pydantic import BaseModel

import os
from dotenv import load_dotenv

load_dotenv()
app = FastAPI()


os.makedirs(os.getenv("DATA_DIR"), exist_ok=True)


class AnalysisRequest(BaseModel):
    url: str

@app.post("/analyze_video")
async def analyze_video(request: AnalysisRequest):
    result = utils.fetch_and_analyze(request.url)
    utils.save_to_csv(result)
    return result