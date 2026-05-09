import pandas as pd
from typing import Dict, Any
import logging

from pubmed_supervisor import (
    search_pubmed,
    fetch_details,
    extract_info,
    extract_country,
    unify_authors,
    merge_with_scimago
)
from .schemas import ResultRow

logger = logging.getLogger(__name__)

def run_supervisor_workflow(query: str, from_date: str, to_date: str) -> Dict[str, Any]:
    # 1. Search PubMed
    try:
        # Date format expected by pubmed_supervisor is usually YYYY/MM/DD
        pmids = search_pubmed(query, mindate=from_date, maxdate=to_date)
    except Exception as e:
        logger.error(f"Failed to search pubmed: {e}")
        return {"candidates": [], "metadata": {"error": str(e)}}

    if not pmids:
        return {"candidates": [], "metadata": {"status": "no_results"}}

    # 2. Fetch details (limit to 50 for API responsiveness during dev)
    max_results = 50 
    papers = fetch_details(pmids[:max_results], max_workers=4, delay=0.1)

    # 3. Extract info
    author_rows = extract_info(papers)
    if not author_rows:
        return {"candidates": [], "metadata": {"status": "no_authors_found"}}
        
    df = pd.DataFrame(author_rows)

    # 4. Extract Country
    if "affiliations" in df.columns:
        df["country"] = df["affiliations"].apply(extract_country)
    else:
        df["country"] = ""

    # 5. Unify authors (we'll skip SCImago merge for the basic UI unless requested, to avoid file dependencies)
    # Filter to only those with emails
    if "email" in df.columns:
        df_filtered = df[df["email"].notna()]
    else:
        df_filtered = df

    if df_filtered.empty:
         return {"candidates": [], "metadata": {"status": "no_authors_with_email"}}

    df_unified = unify_authors(df_filtered)

    # Transform to ResultRow
    candidates = []
    for _, row in df_unified.iterrows():
        # dummy score based on num papers
        num_papers = row.get("num_papers", 1)
        score = str(min(100, 50 + num_papers * 10))
        
        # Institution is tricky after unification, usually we might take the first affiliation or leave it blank
        # The frontend expects an institution string.
        
        candidates.append(ResultRow(
            author=str(row.get("author", "")),
            institution=" | ".join(row.get("all_affiliations", [])) if isinstance(row.get("all_affiliations"), list) else str(row.get("all_affiliations", "")),
            country=str(row.get("country", "")),
            email=str(row.get("email", "")),
            score=score,
            num_papers=num_papers,
            papers=row.get("papers", []) if isinstance(row.get("papers"), list) else [],
            journals=row.get("journals", []) if isinstance(row.get("journals"), list) else []
        ))

    return {
        "candidates": candidates,
        "metadata": {
            "total_found": len(pmids),
            "processed": len(papers),
            "unified_authors": len(candidates)
        }
    }
