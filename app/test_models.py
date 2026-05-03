from app.models import SearchResult, CritiqueResult, Finding, AgentMemory, ResearchReport

search_result = SearchResult("It's only search result", "This is the url", "This is the content", "This is the source", "This is the query")
critique_result =  CritiqueResult(0.7, 0.8, ["hello", "world"], 0.8, "just for fun")
finding = Finding(search_result, critique_result)
memory = AgentMemory(0,3,[finding])
research_report = ResearchReport("", ["", ""], ["", "", ""], 0.8, ["", ""], ["", ""])

print(f"Search Result: {search_result} \nCritique Result: {critique_result} \nFindings: {finding} \nAgent Memory: {memory} \nResearch Report: {research_report}\n")