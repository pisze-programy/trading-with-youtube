import os
from dotenv import load_dotenv
from fastapi import FastAPI
from pydantic import BaseModel

import app.utils as utils

load_dotenv()
app = FastAPI()

class AnalysisRequest(BaseModel):
    channel_name: str

@app.post("/analyze_channel")
async def analyze_channel(request: AnalysisRequest):
    result = utils.fetch_and_analyze(request.channel_name)
    return {"status": "success", "data": result}