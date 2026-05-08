"""
Data enrichment functions: SCImago merging, country extraction, author unification.
"""

import re
import pandas as pd
from .utils import first_valid


def merge_with_scimago(df, scimago_file="scimagojr_2025.csv"):
    """
    Merge author DataFrame with SCImago journal rankings.

    Enriches the author dataframe with journal quality metrics by matching on ISSN
    numbers. The SCImago file must be a CSV with semicolon separators.

    Args:
        df (pandas.DataFrame): Author dataframe with 'journal_issn' column.
        scimago_file (str): Path to SCImago CSV file. Default: "scimagojr_2025.csv".

    Returns:
        pandas.DataFrame: Merged dataframe with SCImago columns added.

    Raises:
        FileNotFoundError: If scimago_file does not exist.
        KeyError: If expected columns are missing.

    Example:
        >>> df = pd.read_csv("authors.csv")
        >>> df_merged = merge_with_scimago(df)
        >>> df_merged[['journal_title', 'scimago_rank', 'scimago_sjr']].head()

    Note:
        - One ISSN can map to multiple rows in SCImago (for different ISSN formats).
        - The merge is left outer join (keeps all author records).
        - ISSN comparison strips hyphen characters for flexibility.
    """
    # Load the SCImago data
    df_scimago = pd.read_csv(scimago_file, sep=";", encoding="utf-8")

    # Clean up column names and data
    df_scimago["Title"] = df_scimago["Title"].str.strip()
    df_scimago["Issn"] = df_scimago["Issn"].str.strip()
    issn = df_scimago["Issn"].str.split(", ").explode()
    df_scimago = df_scimago.iloc[issn.index]
    df_scimago["Issn"] = issn.values

    # Select relevant columns to merge
    scimago_cols = [
        "Sourceid",
        "Title",
        "Rank",
        "Type",
        "Issn",
        "Publisher",
        "SJR",
        "SJR Best Quartile",
        "H index",
        "Citations / Doc. (2years)",
        "Categories",
        "Country",
        "Areas",
    ]
    df_scimago = df_scimago[scimago_cols].copy()
    df_scimago = df_scimago.rename(
        columns={
            "Sourceid": "scimago_sourceid",
            "Title": "scimago_title",
            "Rank": "scimago_rank",
            "Type": "scimago_type",
            "Issn": "scimago_issn",
            "Publisher": "scimago_publisher",
            "SJR": "scimago_sjr",
            "SJR Best Quartile": "scimago_sjr_quartile",
            "H index": "scimago_h_index",
            "Citations / Doc. (2years)": "scimago_citations_per_doc_2yr",
            "Categories": "scimago_categories",
            "Country": "scimago_country",
            "Areas": "scimago_areas",
        }
    )

    df_merged = df.merge(
        df_scimago,
        left_on=df["journal_issn"].str.replace("-", ""),
        right_on=df_scimago["scimago_issn"],
        how="left",
    ).drop(columns=["key_0"])

    return df_merged


def extract_country(affiliations):
    """
    Extract country from affiliation string(s) using regex matching.

    Searches affiliation text for country names using a comprehensive dictionary
    of regex patterns covering major countries across all continents.

    Args:
        affiliations (str, list, or None): Single affiliation string or list of
            affiliation strings.

    Returns:
        str: Extracted country name (e.g., "United States", "Germany") or
            "Other" if no match found.

    Examples:
        >>> extract_country("Department of CS, MIT, USA")
        'United States'

        >>> extract_country(["University of Tokyo", "Japan"])
        'Japan'

        >>> extract_country(None)
        'Other'

    Note:
        - Case-insensitive matching.
        - Returns first matching country found.
        - Returns "Other" if no country patterns match.
        - Includes patterns for 60+ countries worldwide.
    """
    if not affiliations or (isinstance(affiliations, list) and not any(affiliations)):
        return "Other"

    # Convert to list if needed
    if isinstance(affiliations, str):
        aff_list = [affiliations]
    else:
        aff_list = affiliations if isinstance(affiliations, list) else []

    # Common countries to look for
    country_patterns = {
        # --- North America ---
        "United States": r"\b(usa|u\.s\.a\.?|united states|united states of america)\b",
        "Canada": r"\b(canada|canadian)\b",
        "Mexico": r"\b(mexico|mexican)\b",
        # --- Europe ---
        "United Kingdom": r"\b(united kingdom|u\.k\.?|england|scotland|wales|northern ireland)\b",
        "Germany": r"\b(germany|deutschland|german)\b",
        "France": r"\b(france|français|french)\b",
        "Italy": r"\b(italy|italian)\b",
        "Spain": r"\b(spain|spanish)\b",
        "Netherlands": r"\b(netherlands|dutch|holland)\b",
        "Switzerland": r"\b(switzerland|swiss)\b",
        "Belgium": r"\b(belgium|belgian)\b",
        "Austria": r"\b(austria|austrian)\b",
        "Sweden": r"\b(sweden|swedish)\b",
        "Norway": r"\b(norway|norwegian)\b",
        "Denmark": r"\b(denmark|danish)\b",
        "Finland": r"\b(finland|finnish)\b",
        "Ireland": r"\b(ireland|irish)\b",
        "Poland": r"\b(poland|polish)\b",
        "Portugal": r"\b(portugal|portuguese)\b",
        "Greece": r"\b(greece|greek)\b",
        "Czech Republic": r"\b(czech|czechia)\b",
        "Hungary": r"\b(hungary|hungarian)\b",
        # --- Asia ---
        "China": r"\b(china|people'?s republic of china|p\.?r\.?\s*china|pr china)\b",
        "Japan": r"\b(japan|japanese)\b",
        "South Korea": r"\b(south korea|korea|korean)\b",
        "India": r"\b(india|indian)\b",
        "Singapore": r"\b(singapore|singaporean)\b",
        "Taiwan": r"\b(taiwan|taiwanese)\b",
        "Hong Kong": r"\b(hong kong)\b",
        "Israel": r"\b(israel|israeli)\b",
        "Saudi Arabia": r"\b(saudi arabia|saudi)\b",
        "United Arab Emirates": r"\b(u\.?a\.?e\.?|united arab emirates|dubai|abu dhabi)\b",
        "Turkey": r"\b(turkey|turkish)\b",
        "Thailand": r"\b(thailand|thai)\b",
        "Malaysia": r"\b(malaysia|malaysian)\b",
        "Indonesia": r"\b(indonesia|indonesian)\b",
        "Vietnam": r"\b(vietnam|vietnamese)\b",
        "Pakistan": r"\b(pakistan|pakistani)\b",
        "Bangladesh": r"\b(bangladesh|bangladeshi)\b",
        "Iran": r"\b(iran|iranian|persia|persian)\b",
        # --- Oceania ---
        "Australia": r"\b(australia|australian)\b",
        "New Zealand": r"\b(new zealand)\b",
        # --- South America ---
        "Brazil": r"\b(brazil|brazilian)\b",
        "Argentina": r"\b(argentina|argentine|argentinian)\b",
        "Chile": r"\b(chile|chilean)\b",
        "Colombia": r"\b(colombia|colombian)\b",
        "Peru": r"\b(peru|peruvian)\b",
        # --- Africa ---
        "South Africa": r"\b(south africa|south african)\b",
        "Egypt": r"\b(egypt|egyptian)\b",
        "Nigeria": r"\b(nigeria|nigerian)\b",
        "Kenya": r"\b(kenya|kenyan)\b",
        "Morocco": r"\b(morocco|moroccan)\b",
        "Ghana": r"\b(ghana|ghanaian)\b",
        # --- Russia & Eastern Europe ---
        "Russia": r"\b(russia|russian|federation)\b",
        "Ukraine": r"\b(ukraine|ukrainian)\b",
    }

    for aff in aff_list:
        if not aff:
            continue
        aff_lower = aff.lower()
        for country, pattern in country_patterns.items():
            if re.search(pattern, aff_lower, re.IGNORECASE):
                return country

    return "Other"


def unify_authors(df):
    """
    Create a unified view of each author with their papers and affiliations.

    Aggregates the author dataframe (one row per author per article) into a
    unified view with one row per unique author. Combines papers, affiliations,
    journals, and other information across all records for each author.

    Args:
        df (pandas.DataFrame): Author dataframe with at least: author, title,
            affiliations, email, country, journal_title, pmid.

    Returns:
        pandas.DataFrame: Unified authors dataframe with columns:
            - author: Author name
            - email: First valid email address
            - country: First valid country
            - all_affiliations: List of all unique affiliations
            - papers: List of all unique paper titles
            - journals: List of all unique journals
            - num_papers: Count of unique papers

    Example:
        >>> df = extract_info(papers)  # Has 500 rows (many authors repeat)
        >>> df_unified = unify_authors(df)
        >>> len(df_unified)  # Fewer rows, one per unique author
        127
        >>> df_unified.loc[0, 'num_papers']
        5

    Note:
        - Rows are sorted by num_papers (descending) - most prolific authors first.
        - Affiliations are deduplicated per author.
        - Emails and countries use first valid (non-null) value.
    """
    # Group by author name
    author_groups = df.groupby("author").agg({
        "title": lambda x: list(x.unique()),
        "affiliations": lambda x: list(
            set(
                [
                    a
                    for affs in x
                    for a in (affs if isinstance(affs, list) else [affs])
                    if a
                ]
            )
        ),
        "email": lambda x: first_valid(x),
        "country": lambda x: first_valid(x),
        "journal_title": lambda x: list(x.unique()),
        "pmid": "nunique",
    }).reset_index()

    # Rename columns
    author_groups = author_groups.rename(columns={
        "title": "papers",
        "affiliations": "all_affiliations",
        "email": "email",
        "country": "country",
        "journal_title": "journals",
        "pmid": "num_papers",
    })

    # Sort by number of papers (descending)
    author_groups = author_groups.sort_values("num_papers", ascending=False)

    return author_groups
