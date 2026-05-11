import pandas as pd
from typing import Dict, Any
import re
import logging
import sys
from pathlib import Path

# Allow running API from repository root without requiring `pip install -e .`.
try:
    from pubmed_supervisor import (
        search_pubmed,
        fetch_details,
        extract_info,
        extract_country,
        unify_authors,
        merge_with_scimago,
    )
except ModuleNotFoundError:
    repo_src = Path(__file__).resolve().parents[1] / "src"
    if str(repo_src) not in sys.path:
        sys.path.insert(0, str(repo_src))
    from pubmed_supervisor import (
        search_pubmed,
        fetch_details,
        extract_info,
        extract_country,
        unify_authors,
        merge_with_scimago,
    )
from .schemas import ResultRow, PaperDetail

logger = logging.getLogger(__name__)

# Regex to extract keyword text from Biopython StringElement repr strings.
# extraction.py calls str() on ListElement objects, producing strings like:
#   "ListElement([StringElement('keyword', attributes={...}), ...], ...)"
# This pattern pulls the bare keyword text from each StringElement('...').
_STRING_ELEMENT_RE = re.compile(r"StringElement\('([^']*)'")

def _parse_keywords(raw_list):
    """Extract clean keyword strings from the raw keywords list."""
    keywords = set()
    for item in raw_list:
        s = str(item)
        matches = _STRING_ELEMENT_RE.findall(s)
        if matches:
            keywords.update(matches)
        elif s and not s.startswith("ListElement") and not s.startswith("["):
            keywords.add(s)
    return keywords

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

    # Build a lookup of per-paper detail keyed by (author, title)
    paper_detail_map: Dict[str, list] = {}
    keyword_map: Dict[str, set] = {}
    for _, row in df.iterrows():
        author_name = row.get("author", "")
        if author_name not in paper_detail_map:
            paper_detail_map[author_name] = []
            keyword_map[author_name] = set()

        paper_detail_map[author_name].append(PaperDetail(
            title=str(row.get("title", "")),
            pmid=str(row.get("pmid", "")),
            doi=row.get("doi") if pd.notna(row.get("doi")) else None,
            pmc_id=row.get("pmc_id") if pd.notna(row.get("pmc_id")) else None,
            journal_title=str(row.get("journal_title", "")),
            journal_iso=str(row.get("journal_iso", "")),
            journal_volume=str(row.get("journal_volume", "")),
            journal_issue=str(row.get("journal_issue", "")),
            pub_year=str(row.get("pub_year", "")),
            pub_month=str(row.get("pub_month", "")),
            pub_day=str(row.get("pub_day", "")),
            medline_pgn=str(row.get("medline_pgn", "")),
            language=str(row.get("language", "")),
            publication_status=str(row.get("publication_status", "")),
            publication_types=row.get("publication_types", []) if isinstance(row.get("publication_types"), list) else [],
            mesh_headings=row.get("mesh_headings", []) if isinstance(row.get("mesh_headings"), list) else [],
            grants=row.get("grants", []) if isinstance(row.get("grants"), list) else [],
        ))

        kw_list = row.get("keywords", [])
        if isinstance(kw_list, list):
            keyword_map[author_name].update(_parse_keywords(kw_list))

    # Transform to ResultRow with enriched data
    candidates = []
    for _, row in df_unified.iterrows():
        author_name = str(row.get("author", ""))
        num_papers = row.get("num_papers", 1)
        has_email = 1 if row.get("email") else 0

        details = paper_detail_map.get(author_name, [])

        # Deduplicate paper_details by pmid
        seen_pmids: set = set()
        unique_details: list = []
        for d in details:
            if d.pmid and d.pmid in seen_pmids:
                continue
            if d.pmid:
                seen_pmids.add(d.pmid)
            unique_details.append(d)

        unique_journals = set(d.journal_title for d in unique_details if d.journal_title)

        score_val = (
            num_papers * 15
            + has_email * 20
            + min(len(unique_journals), 5) * 5
        )
        score = str(min(100, score_val))

        candidates.append(ResultRow(
            author=author_name,
            institution=" | ".join(row.get("all_affiliations", [])) if isinstance(row.get("all_affiliations"), list) else str(row.get("all_affiliations", "")),
            country=str(row.get("country", "")),
            email=str(row.get("email", "")),
            score=score,
            num_papers=num_papers,
            papers=row.get("papers", []) if isinstance(row.get("papers"), list) else [],
            paper_details=unique_details,
            journals=row.get("journals", []) if isinstance(row.get("journals"), list) else [],
            keywords=sorted(keyword_map.get(author_name, set())),
        ))

    return {
        "candidates": candidates,
        "metadata": {
            "total_found": len(pmids),
            "processed": len(papers),
            "unified_authors": len(candidates)
        }
    }
