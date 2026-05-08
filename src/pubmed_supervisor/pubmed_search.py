"""
PubMed search and fetch functionality.

This module provides functions to search PubMed with automatic date-range splitting
and fetch detailed article information in parallel.
"""

import time
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor

from Bio import Entrez
from tqdm import tqdm

from .config import ENTREZ_EMAIL, RATE_LIMIT_DELAY, MAX_RETRIES, DEFAULT_WORKERS


def search_pubmed(query, mindate="2024/01/01", maxdate="2030/01/01"):
    """
    Recursively search PubMed by splitting date range when results exceed 10,000.

    The PubMed esearch API has a hard limit of 10,000 results per query. This function
    handles this limitation by automatically splitting the date range in half when the
    result count approaches this limit, then recursively searching both halves.

    Args:
        query (str): PubMed search query (e.g., '"machine learning"[tiab]').
        mindate (str): Start date in YYYY/MM/DD format. Default: "2024/01/01".
        maxdate (str): End date in YYYY/MM/DD format. Default: "2030/01/01".

    Returns:
        list: List of all unique PMIDs found (str), preserving order.

    Raises:
        Exception: If PubMed API is unreachable or returns errors.

    Examples:
        >>> pmids = search_pubmed(
        ...     '"deep learning"[tiab]',
        ...     mindate="2024/01/01",
        ...     maxdate="2024/12/31"
        ... )
        >>> len(pmids)
        1234

    Note:
        - Requires ENTREZ_EMAIL to be set in config or environment variable.
        - Respects NCBI rate limits with automatic delays.
        - Duplicates are automatically removed while preserving order.
    """
    Entrez.email = ENTREZ_EMAIL

    def search_range(q, start_str, end_str):
        """Recursive helper function."""
        # Format for Entrez
        start_dt = datetime.strptime(start_str.replace("/", "-"), "%Y-%m-%d")
        end_dt = datetime.strptime(end_str.replace("/", "-"), "%Y-%m-%d")

        # Calculate days in range
        days = (end_dt - start_dt).days

        try:
            handle = Entrez.esearch(
                db="pubmed",
                term=q,
                retmax=10_000,
                datetype="pdat",
                mindate=start_str,
                maxdate=end_str,
            )
            record = Entrez.read(handle)
            handle.close()

            ids = record.get("IdList", [])

        except Exception as e:
            print(f"  Error searching {start_str} to {end_str}: {e}")
            return []

        # If results < 10,000 or range is <= 1 day, return results
        if len(ids) < 9999 or days <= 1:
            print(f"  ✓ {start_str} → {end_str}: {len(ids)} papers")
            return ids

        # Results exceed limit, split the period in half
        mid_dt = start_dt + timedelta(days=(days // 2))
        mid_str = mid_dt.strftime("%Y/%m/%d")

        print(
            f"  ⚠ {start_str} → {end_str}: {len(ids)} papers (exceeds limit, splitting...)"
        )

        # Recursively search both halves
        left_results = search_range(q, start_str, mid_str)
        right_results = search_range(q, mid_str, end_str)

        return left_results + right_results

    # Start recursive search
    print(f"\n--- Starting recursive search: {mindate} to {maxdate} ---")
    all_ids = search_range(query, mindate, maxdate)

    # Remove duplicates while preserving order
    unique_ids = list(dict.fromkeys(all_ids))
    print(f"\n✓ Total unique PMIDs found: {len(unique_ids)}")
    return unique_ids


def fetch_details(pmids, max_workers=None, delay=None, max_retries=None):
    """
    Fetch detailed article information from PubMed in parallel with retry logic.

    Fetches XML records for multiple PMIDs in parallel, with automatic retries
    on failure using exponential backoff. Results are chunked into groups of 1000
    to respect PubMed API limits.

    Args:
        pmids (list): List of PubMed IDs (as strings).
        max_workers (int, optional): Number of parallel workers. Default from config.
        delay (float, optional): Delay in seconds between requests. Default from config.
        max_retries (int, optional): Max retry attempts per chunk. Default from config.

    Returns:
        list: List of PubmedArticle XML objects (dicts).

    Examples:
        >>> pmids = ["12345678", "87654321"]
        >>> papers = fetch_details(pmids, max_workers=2)
        >>> len(papers)
        2

    Note:
        - Results are chunked into groups of 1000 PMIDs.
        - Failed chunks are retried with exponential backoff.
        - Uses ThreadPoolExecutor for parallel fetching.
    """
    if max_workers is None:
        max_workers = DEFAULT_WORKERS
    if delay is None:
        delay = RATE_LIMIT_DELAY
    if max_retries is None:
        max_retries = MAX_RETRIES

    Entrez.email = ENTREZ_EMAIL
    papers = []
    chunks = [pmids[i : i + 1000] for i in range(0, len(pmids), 1000)]

    def fetch_chunk(chunk_ids, attempt=0):
        try:
            time.sleep(delay)  # Rate limiting
            ids = ",".join(chunk_ids)
            handle = Entrez.efetch(
                db="pubmed", id=ids, rettype="xml", retmode="text"
            )
            chunk_papers = Entrez.read(handle)
            handle.close()
            return chunk_papers.get("PubmedArticle", [])
        except Exception as e:
            if attempt < max_retries:
                print(f"  ⚠ Retry {attempt + 1}/{max_retries} for chunk")
                time.sleep(delay * (attempt + 2))  # Exponential backoff
                return fetch_chunk(chunk_ids, attempt + 1)
            else:
                print(f"  ✗ Failed after {max_retries} retries")
                return []

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        results = list(
            tqdm(
                executor.map(lambda c: fetch_chunk(c, 0), chunks),
                desc="Fetching papers",
                total=len(chunks),
            )
        )

    for result in results:
        papers.extend(result)

    print(f"✓ Retrieved {len(papers)} papers from {len(pmids)} PMIDs")
    return papers
