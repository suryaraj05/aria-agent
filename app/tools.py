from typing import List
from app.models import SearchResult, CritiqueResult
from ddgs import DDGS
import requests
from bs4 import BeautifulSoup
from google.genai import client as genai_client
import json

def search_web(query: str) -> List[SearchResult]:
    results_list = []
    with DDGS() as ddgs:
        results = ddgs.text(query, max_results=3)

    for r in results:
        if "title" not in r or "href" not in r or "body" not in r:
            continue
        content = fetch_page(r["href"])
        if not content:
            continue
        results_list.append(SearchResult(
            title = r["title"],
            url = r["href"],
            content = content,
            source = "duckduckgo",
            query = query
        ))

    return results_list


def fetch_page(url: str) -> str:
    try:
        response = requests.get(url, timeout=10)
        if response.status_code != 200:
            return ""
        soup = BeautifulSoup(response.text, "html.parser")
        text = soup.get_text()
        clean_text = " ".join(text.split())
        if not clean_text:
            return ""
        return clean_text[:2000]
    except Exception as e:
        print(f"[ERROR] fetch_page failed: {e}")
        return ""
    

def critique_finding(result: SearchResult, client: genai_client.Client) -> CritiqueResult:
    prompt = f"""
You are an expert research evaluator.

Your task is to evaluate the following content with respect to the query.

Query:
{result.query}

Content:
{result.content}

Evaluate:
- relevance_score (float between 0 and 1)
- accuracy_score (float between 0 and 1)
- gaps (list of missing or unclear aspects)
- confidence (float between 0 and 1)
- reasoning (brief explanation)

Return ONLY valid JSON in this format:

{{
  "relevance_score": 0.8,
  "accuracy_score": 0.7,
  "gaps": ["missing recent data"],
  "confidence": 0.75,
  "reasoning": "The content is relevant but lacks..."
}}
"""
    response = client.models.generate_content(
        model="models/gemini-2.5-flash",
        contents=[prompt],
    )
    if not response.text:
        return CritiqueResult(0.0, 0.0, [], 0.0, "")
    raw_response = response.text

    clean_json_str = raw_response.replace("```json", "").replace("```", "").strip()
    try:
        data = json.loads(clean_json_str)

        score = data.get("relevance_score", 0.0)
        
        print(f"Success! Relevance Score: {score}")

    except json.JSONDecodeError as e:
        print(f"Failed to parse JSON. Raw output was: {raw_response}")
        return CritiqueResult(0.0, 0.0, [], 0.0, "parsing_failed")
    return CritiqueResult(data.get("relevance_score", 0.0), data.get("accuracy_score", 0.0), data.get("gaps", []), data.get("confidence", 0.0), data.get("reasoning", ""))