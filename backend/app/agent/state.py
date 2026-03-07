from typing import TypedDict, List

class AgentState(TypedDict):
    question: str
    context: List[str]  # Retrieved HR documents
    answer: str
    relevance_score: str # "yes" or "no" (graded by the LLM)