from typing import List
import json
from app.models import AgentMemory, Finding, ResearchReport
from app.tools import search_web, critique_finding


def _plan(self, query: str) -> List[str]:
    prompt = f"""
You are a Research Planner.

Your task is to break the following research question into 3-5 sub-questions.

Question:
{query}

Return ONLY a JSON list of strings.

Example:
["question 1", "question 2", "question 3"]
"""
    response = self.client.models.generate_content(
        model="models/gemini-2.5-flash",
        contents=[prompt],
    )

    if not response.text:
        return []
    raw_response = response.text

    clean_json_str = raw_response.replace("```json", "").replace("```", "").strip()
    try:
        data = json.loads(clean_json_str)
        
        if isinstance(data, list):
            print(f"Success! questions are divided")
            return data
        return []

    except json.JSONDecodeError as e:
        print(f"Failed to convert into sub questions. Raw output was: {raw_response}")
        return []
   
def _research_loop(self, sub_questions: List[str]) -> AgentMemory:
    memory = AgentMemory()
    for question in sub_questions:
        print(f"[LOOP] Question: {question}")
        memory.iteration += 1
        if memory.iteration >= memory.max_iterations+1:
            break
        results = search_web(question)
        if not results:
            continue
        
        for result in results:
            critique = critique_finding(result, self.client)
            finding =  Finding(result, critique)
            memory.findings.append(finding)

    return memory


def _reflect(self, memory: AgentMemory) -> float:
    confidences = [
        finding.critique.confidence
        for finding in memory.findings
    ]
    if not confidences:
        return 0.0
    else:
        return float(sum(confidences))/float(len(confidences))


def _synthesize(self, memory: AgentMemory, confidence: float) -> ResearchReport:
    research_report = ResearchReport()