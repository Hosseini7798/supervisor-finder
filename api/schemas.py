from pydantic import BaseModel
from typing import List, Dict, Any, Optional

class SearchRequest(BaseModel):
    query: str
    from_date: str
    to_date: str

class PaperDetail(BaseModel):
    title: str
    pmid: str = ""
    doi: Optional[str] = None
    pmc_id: Optional[str] = None
    journal_title: str = ""
    journal_iso: str = ""
    journal_volume: str = ""
    journal_issue: str = ""
    pub_year: str = ""
    pub_month: str = ""
    pub_day: str = ""
    medline_pgn: str = ""
    language: str = ""
    publication_status: str = ""
    publication_types: List[str] = []
    mesh_headings: List[Dict[str, str]] = []
    grants: List[Dict[str, str]] = []

class ResultRow(BaseModel):
    author: str
    institution: str
    country: str
    email: str
    score: str
    num_papers: int = 0
    papers: List[str] = []
    paper_details: List[PaperDetail] = []
    journals: List[str] = []
    keywords: List[str] = []

class SearchResponse(BaseModel):
    candidates: List[ResultRow]
    metadata: Dict[str, Any]
