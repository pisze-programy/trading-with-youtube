import os
from dotenv import load_dotenv
from fastapi import FastAPI
from pydantic import BaseModel

import app.utils as utils

load_dotenv()
app = FastAPI()

class AnalysisRequest(BaseModel):
    url: str

@app.post("/analyze_video")
async def analyze_video(request: AnalysisRequest):
    result = utils.fetch_and_analyze(request.url)
    utils.save_to_file(result)
    return result