from pydantic import BaseModel
from typing import List, Dict, Any

class SearchRequest(BaseModel):
    query: str
    from_date: str
    to_date: str

class ResultRow(BaseModel):
    author: str
    institution: str
    country: str
    email: str
    score: str
    num_papers: int = 0
    papers: List[str] = []
    journals: List[str] = []

class SearchResponse(BaseModel):
    candidates: List[ResultRow]
    metadata: Dict[str, Any]
