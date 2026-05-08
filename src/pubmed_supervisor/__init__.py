"""
supervisor-finder: Find academic supervisors from published articles.

A Python package for searching PubMed articles, extracting author information,
and identifying potential supervisors based on publication history, country,
and journal quality metrics.
"""

__version__ = "0.1.0"
__author__ = "Your Name"
__email__ = "your.email@example.com"

from .pubmed_search import search_pubmed, fetch_details
from .extraction import extract_info
from .enrichment import merge_with_scimago, extract_country, unify_authors
from .doi_lookup import find_corresponding_author_from_doi

__all__ = [
    "search_pubmed",
    "fetch_details",
    "extract_info",
    "merge_with_scimago",
    "extract_country",
    "unify_authors",
    "find_corresponding_author_from_doi",
]
