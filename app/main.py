from fastapi import FastAPI
from app.agent import ARIAAgent
from google import genai
import os
from dataclasses import asdict
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv('app/.env')

class QueryRequest(BaseModel):
    query: str

app = FastAPI()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
agent = ARIAAgent(client)

@app.post("/research")
def research(request: QueryRequest):
    report = agent.run(request.query)
    return asdict(report)
