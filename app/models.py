from dataclasses import dataclass, field
from typing import List

@dataclass
class SearchResult:
    """
    Represents a single search result fetched from the web.
    """
    title: str
    url: str
    content: str
    source: str
    query: str

@dataclass
class CritiqueResult:
    """
    Represents the LLM's evaluation of a fetched piece of content.
    """
    # how relevant the query is
    relevance_score: float
    #estimated correctness
    accuracy_score: float
    #what is missing
    gaps: List[str]
    #overall trust
    confidence: float
    reasoning: str

@dataclass
class Finding:
    """
    One evaluated piece of information
    """
    result: SearchResult
    critique: CritiqueResult

@dataclass
class AgentMemory:
    iteration: int = 0
    max_iterations: int = 3
    findings: List[Finding] = field(default_factory=list)

@dataclass
class ResearchReport:
    summary: str
    key_points: List[str]
    contradictions: List[str]
    confidence_score: float
    sources: List[str]
    gaps: List[str]