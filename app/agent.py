from typing import List
import json
from app.models import AgentMemory, Finding, ResearchReport
from app.tools import search_web, critique_finding


class ARIAAgent:
    def __init__(self, client):
        self.client =  client
        
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
            if memory.iteration > memory.max_iterations:
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
        fallback = f"Research completed on {len(memory.findings)} findings"

        memory.findings = sorted(
            memory.findings,
            key=lambda f: f.critique.confidence,
            reverse=True
        )
        formatted_findings = "\n\n".join([
            f"""
Content: {finding.result.content[:200]}
Source: {finding.result.url}
Confidence: {finding.critique.confidence}
Gaps: {finding.critique.gaps}
            """
            for finding in memory.findings[:5]
       ] )
        prompt = f"""
You are an expert research analyst.

Given the following findings:

{formatted_findings}

Synthesize a structured report with:
- summary
- key_points (list)
- contradictions (list)
- sources (list)
- gaps (list)

Use the provided confidence score: {confidence}

Key points must:
- combine multiple findings
- avoid generic definitions
- include specific insights

Return ONLY valid JSON in this format:
{{
  "summary": "...",
  "key_points": ["..."],
  "contradictions": ["..."],
  "confidence_score": {confidence},
  "sources": ["..."],
  "gaps": ["..."]
}}

Do NOT include markdown or backticks.
"""     
        print(f"[SYNTHESIZE] Findings used: {len(memory.findings)}")
        response = self.client.models.generate_content(
            model = "models/gemini-2.5-flash",
            contents =[prompt]
        )
        if not response.text:
            return ResearchReport("No response text found", [], [], 0.0, [], [])
        raw_response = response.text
        clean_json_str = raw_response.replace("```json", "").replace("```", "").strip()
        try:
            data = json.loads(clean_json_str)
            summary = data.get("summary", fallback)

            key_points = data.get("key_points", [])
            if not isinstance(key_points, list):
                key_points = [str(key_points)]
            key_points = key_points[:5]
                
            contradictions = data.get("contradictions", [])
            if not isinstance(contradictions, list):
                contradictions = [str(contradictions)]
            contradictions = contradictions[:5]

            try:
                confidence = float(data.get("confidence_score", confidence))
                confidence = round(confidence, 2)
            except (TypeError, ValueError):
                pass

            sources = data.get("sources", [])
            if not isinstance(sources, list):
                sources = [str(sources)]
            sources = [s.strip() for s in sources if s.startswith("http")]
            
            gaps = data.get("gaps", [])
            if not isinstance(gaps, list):
                gaps = [str(gaps)]
            gaps = gaps[:5]

            gaps = list(dict.fromkeys(gaps))
            sources = list(dict.fromkeys(sources))

            research_report = ResearchReport(summary, key_points, contradictions, confidence,sources , gaps)
            return research_report
        except json.JSONDecodeError as e:
            print(f"Failed to parse JSON. Raw output was: {raw_response}")
            return ResearchReport("No sufficient data found", [], [], 0.0, [], [])


    def run(self, query: str) -> ResearchReport:
        sub_questions = self._plan(query)
        if not sub_questions:
            return ResearchReport("No sufficient data found", [], [], 0.0, [], [])
        memory = self._research_loop(sub_questions)
        if not memory.findings:
            return ResearchReport("No sufficient data found", [], [], 0.0, [], [])
        confidence = self._reflect(memory)
        report = self._synthesize(memory, confidence)
        return report

