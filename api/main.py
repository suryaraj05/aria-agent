from fastapi import FastAPI

from ..app.agent import ARIAAgent

app = FastAPI()


@app.get("/research")
def research(query: str):
    agent = ARIAAgent(api_key="")
    report = agent.generate_report(query)
    return {"query": query, "report": report}
