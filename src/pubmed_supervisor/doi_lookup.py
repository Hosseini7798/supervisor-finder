"""
Corresponding author lookup via DOI web scraping.

This module fetches article pages from DOI URLs and extracts corresponding author
information using meta tag parsing and JSON-LD schema extraction.
"""

import re
import json
import requests
from bs4 import BeautifulSoup


def find_corresponding_author_from_doi(doi, pubmed_authors=None):
    """
    Extract corresponding author(s) from an article page via DOI.

    Fetches the article page from doi.org and extracts author information from:
    1. Meta tags (citation_author, citation_author_email)
    2. JSON-LD schema data
    3. Fallback: email pattern search in page text

    Optionally matches extracted names with PubMed author names for consistency.

    Args:
        doi (str): DOI identifier (e.g., "10.1234/example").
        pubmed_authors (list, optional): List of author names from PubMed to match
            against for name normalization.

    Returns:
        list or None: List of dicts with 'name' and 'email' keys for corresponding
            author(s), or None if no emails found. Each dict has:
            - 'name' (str or None): Author name if available
            - 'email' (str): Email address

    Examples:
        >>> corr_authors = find_corresponding_author_from_doi("10.1234/example")
        >>> corr_authors
        [{'name': 'John Smith', 'email': 'john@example.com'}]

        >>> # With PubMed author names for name matching
        >>> corr_authors = find_corresponding_author_from_doi(
        ...     "10.1234/example",
        ...     pubmed_authors=["John Smith", "Jane Doe"]
        ... )

    Note:
        - DOI URLs are resolved via https://doi.org/{doi}
        - Filters out system emails (e.g., @springernature.com, @rights)
        - Returns first matching email if fallback text search is used
        - Handles both single and multiple corresponding authors
        - Timeout: 15 seconds per request
    """
    if not doi:
        return None

    url = f"https://doi.org/{doi}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }

    try:
        resp = requests.get(url, headers=headers, timeout=15)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        # Collect ALL author emails from meta tags
        author_emails = []
        for meta in soup.find_all("meta", {"name": "citation_author_email"}):
            email = meta.get("content", "").strip()
            if email:
                author_emails.append(email)

        # Collect ALL author names from meta tags
        author_names_from_doi = []
        for meta in soup.find_all("meta", {"name": "citation_author"}):
            name = meta.get("content", "").strip()
            if name:
                author_names_from_doi.append(name)

        # Build list of corresponding authors by pairing names with emails
        corresponding_authors = []

        if author_emails:
            # If we have emails, try to match with names
            for i, email in enumerate(author_emails):
                name = (
                    author_names_from_doi[i]
                    if i < len(author_names_from_doi)
                    else None
                )

                # If pubmed_authors provided, try to find matching author
                if pubmed_authors and name:
                    name_lower = name.lower()
                    matched = False
                    for pub_author in pubmed_authors:
                        pub_author_lower = pub_author.lower()
                        # Check if last name matches or full name contains
                        name_parts = name_lower.split()
                        if name_parts:
                            last_name = name_parts[-1]
                            if (last_name in pub_author_lower or
                                pub_author_lower in name_lower):
                                name = pub_author  # Use PubMed version
                                matched = True
                                break
                    if not matched:
                        pass  # Still include if we have email

                corresponding_authors.append({"name": name, "email": email})
        else:
            # Fallback: search for email pattern in page text
            email_pattern = re.compile(r"[\w\.-]+@[\w\.-]+\.\w+")
            page_text = soup.get_text()
            matches = email_pattern.findall(page_text)
            if matches:
                exclude_patterns = [
                    "@copyright",
                    "@rights",
                    "@permissions",
                    "@springernature.com",
                    "@nature.com",
                ]
                for email in matches:
                    if not any(
                        excl in email.lower() for excl in exclude_patterns
                    ):
                        corresponding_authors.append(
                            {"name": None, "email": email}
                        )
                        break  # Only take first valid email

        # Also check JSON-LD schema for additional authors
        for script in soup.find_all("script", type="application/ld+json"):
            try:
                data = json.loads(script.string)
                if isinstance(data, dict):
                    main_entity = data.get("mainEntity", {})
                    for author in main_entity.get("author", []):
                        if isinstance(author, dict):
                            email = author.get("email")
                            name = author.get("name")
                            if email:
                                # Check if not already in our list
                                if not any(
                                    a.get("email") == email
                                    for a in corresponding_authors
                                ):
                                    corresponding_authors.append(
                                        {"name": name, "email": email}
                                    )
            except Exception:
                continue

        return corresponding_authors if corresponding_authors else None

    except Exception as e:
        print(f"Error processing DOI {doi}: {e}")
        return None
