"""
Article and author information extraction from PubMed XML records.

This module extracts comprehensive information from PubMed article records including
paper metadata, author details, affiliations, and article classification.
"""

import re


def extract_info(papers):
    """
    Extract comprehensive author and article information from PubMed efetch results.

    Processes PubMed XML records and creates one row per author, combining article-level
    metadata (PMID, DOI, title, journal info) with author-level details (name, affiliation,
    email) and article classification (MeSH headings, keywords, publication types).

    Args:
        papers (list): List of PubmedArticle XML objects from Entrez.read().

    Returns:
        list: List of dicts, one per author per article, with keys:
            - Paper metadata: pmid, doi, pmc_id, title, journal_title, journal_iso,
              journal_issn, journal_volume, journal_issue, pub_year, pub_month,
              pub_day, medline_pgn, pagination, language, publication_status,
              publication_types
            - Author details: author, last_name, fore_name, initials, author_role,
              valid_yn
            - Affiliation details: affiliations (list), affiliation_identifiers (list),
              email
            - Article classification: mesh_headings (list of dicts), keywords (list)
            - Grant information: grants (list of dicts)

    Examples:
        >>> # papers is output from fetch_details()
        >>> rows = extract_info(papers)
        >>> len(rows)  # One row per author per article
        547
        >>> rows[0].keys()
        dict_keys(['pmid', 'doi', 'author', 'journal_title', ...])

    Note:
        - Collective authors (groups) are skipped.
        - Email is extracted from affiliation strings using regex.
        - MeSH headings include descriptor UI codes.
        - Multiple affiliations per author are stored as lists.
    """
    rows = []
    email_pattern = re.compile(r"[\w\.-]+@[\w\.-]+\.\w+")

    for paper in papers:
        medline_citation = paper.get("MedlineCitation", {})
        article = medline_citation.get("Article", {})
        pmid = (
            medline_citation.get("PMID", "").title()
            if medline_citation.get("PMID")
            else ""
        )

        # --- Extract Article-level metadata ---
        article_title = str(article.get("ArticleTitle", ""))

        # Journal information
        journal = article.get("Journal", {})
        journal_title = journal.get("Title", "")
        journal_iso = journal.get("ISOAbbreviation", "")
        journal_issn = journal.get("ISSN", "")
        journal_volume = journal.get("JournalIssue", {}).get("Volume", "")
        journal_issue = journal.get("JournalIssue", {}).get("Issue", "")
        pub_date = journal.get("JournalIssue", {}).get("PubDate", {})
        pub_year = pub_date.get("Year", "")
        pub_month = pub_date.get("Month", "")
        pub_day = pub_date.get("Day", "")

        # Pagination and publication details
        pagination = article.get("Pagination", {})
        medline_pgn = pagination.get("MedlinePgn", "")
        pagination_info = pagination.get("Pagination", "")

        # Language and publication status
        language = (
            article.get("Language", [""])[0]
            if article.get("Language")
            else ""
        )
        publication_status = article.get("PublicationStatus", "")

        # Publication types (list) - handle StringElement objects
        pub_type_list = []
        for pt in article.get("PublicationTypeList", []):
            pt_str = str(pt) if pt else ""
            pub_type_list.append(pt_str)

        # --- Extract Article ID list (DOI, PMC, etc.) ---
        pubmed_data = paper.get("PubmedData", {})
        article_id_list = pubmed_data.get("ArticleIdList", [])

        doi = None
        pmc_id = None
        for aid in article_id_list:
            id_type = aid.attributes.get("IdType", "")
            id_value = str(aid)
            if id_type == "doi":
                doi = id_value
            elif id_type == "pmc":
                pmc_id = id_value

        # --- Extract MeSH Headings ---
        mesh_headings = []
        for mesh in medline_citation.get("MeshHeadingList", []):
            descriptor = mesh.get("DescriptorName", {})
            qualifier = mesh.get("QualifierName", {})

            # Handle both single element and list for qualifier
            if isinstance(qualifier, list):
                qualifier_str = ""
                qualifier_ui = ""
                if qualifier:
                    q = qualifier[0] if qualifier else None
                    qualifier_str = str(q) if q else ""
                    qualifier_ui = (
                        q.attributes.get("UI", "")
                        if q and hasattr(q, "attributes")
                        else ""
                    )
            else:
                qualifier_str = str(qualifier) if qualifier else ""
                qualifier_ui = (
                    qualifier.attributes.get("UI", "")
                    if qualifier and hasattr(qualifier, "attributes")
                    else ""
                )

            mesh_headings.append(
                {
                    "descriptor": str(descriptor),
                    "descriptor_ui": (
                        descriptor.attributes.get("UI", "")
                        if hasattr(descriptor, "attributes")
                        else ""
                    ),
                    "qualifier": qualifier_str,
                    "qualifier_ui": qualifier_ui,
                }
            )

        # --- Extract Keywords ---
        keyword_list = [
            str(kw) for kw in medline_citation.get("KeywordList", [])
        ]

        # --- Extract Grant Information ---
        grant_list = []
        for grant in article.get("GrantList", []):
            grant_list.append(
                {
                    "grant_id": grant.get("GrantId", ""),
                    "agency": grant.get("Agency", ""),
                    "country": grant.get("Country", ""),
                }
            )

        # --- Extract Author information ---
        for author in article.get("AuthorList", []):
            if "CollectiveName" in author:
                continue  # skip group authors

            # Basic author name info
            last = author.get("LastName", "")
            fore = author.get("ForeName", "")
            initials = author.get("Initials", "")
            full_name = f"{fore} {last}".strip()

            # Author role and validation
            author_role = author.get("AuthorRole", "")
            valid_yn = author.get("ValidYN", "")

            # Affiliation info (can have multiple)
            aff_list = []
            aff_ids = []
            for aff_info in author.get("AffiliationInfo", []):
                aff = aff_info.get("Affiliation", "").strip()
                if aff:
                    aff_list.append(aff)
                    # Try to extract identifiers from affiliation
                    aff_id = aff_info.get("Identifier", "")
                    if aff_id:
                        aff_ids.append(aff_id)

            # Extract email from affiliations
            author_email = None
            for aff in aff_list:
                matches = email_pattern.findall(aff)
                if matches:
                    author_email = matches[0]
                    break

            rows.append(
                {
                    # Paper metadata
                    "pmid": pmid,
                    "doi": doi,
                    "pmc_id": pmc_id,
                    "title": article_title,
                    "journal_title": journal_title,
                    "journal_iso": journal_iso,
                    "journal_issn": journal_issn,
                    "journal_volume": journal_volume,
                    "journal_issue": journal_issue,
                    "pub_year": pub_year,
                    "pub_month": pub_month,
                    "pub_day": pub_day,
                    "medline_pgn": medline_pgn,
                    "pagination": pagination_info,
                    "language": language,
                    "publication_status": publication_status,
                    "publication_types": pub_type_list,
                    # Author details
                    "author": full_name,
                    "last_name": last,
                    "fore_name": fore,
                    "initials": initials,
                    "author_role": author_role,
                    "valid_yn": valid_yn,
                    # Affiliation details
                    "affiliations": aff_list,
                    "affiliation_identifiers": aff_ids,
                    "email": author_email,
                    # Article classification
                    "mesh_headings": mesh_headings,
                    "keywords": keyword_list,
                    # Grant information
                    "grants": grant_list,
                }
            )

    return rows
