# API Reference

Complete reference for supervisor-finder functions.

## Module: pubmed_supervisor

### pubmed_supervisor.pubmed_search

#### `search_pubmed(query, mindate='2024/01/01', maxdate='2030/01/01')`

Search PubMed with automatic date-range splitting for large result sets.

**Parameters:**
- `query` (str): PubMed search query using MeSH terms and text qualifiers
  - Example: `'("deep learning"[tiab] OR "neural network"[tiab])'`
- `mindate` (str, optional): Start date in YYYY/MM/DD format
  - Default: `'2024/01/01'`
- `maxdate` (str, optional): End date in YYYY/MM/DD format
  - Default: `'2030/01/01'`

**Returns:**
- `list`: List of unique PMID strings, preserving order

**Raises:**
- `Exception`: If PubMed API is unreachable or returns errors

**Behavior:**
- Automatically splits date ranges when results exceed ~10,000 (PubMed limit)
- Prints progress with `✓`, `⚠`, and `✗` indicators
- Deduplicates results while preserving order

**Example:**
```python
from pubmed_supervisor import search_pubmed

pmids = search_pubmed(
    '("artificial intelligence"[tiab] OR "machine learning"[tiab])',
    mindate='2024/01/01',
    maxdate='2024/12/31'
)
print(f"Found {len(pmids)} articles")
```

---

#### `fetch_details(pmids, max_workers=4, delay=0.1, max_retries=3)`

Fetch detailed XML records for PubMed articles in parallel.

**Parameters:**
- `pmids` (list): List of PubMed IDs as strings
- `max_workers` (int, optional): Number of parallel threads
  - Default: `4` (from config)
- `delay` (float, optional): Delay in seconds between requests
  - Default: `0.1` (respects NCBI rate limits)
- `max_retries` (int, optional): Retry attempts per chunk on failure
  - Default: `3`

**Returns:**
- `list`: List of PubmedArticle XML objects (dicts from Entrez.read)

**Notes:**
- PMIDs are processed in chunks of 1000
- Failed chunks are retried with exponential backoff
- Uses ThreadPoolExecutor for parallel processing
- Each chunk is rate-limited per NCBI guidelines

**Example:**
```python
from pubmed_supervisor import search_pubmed, fetch_details

pmids = search_pubmed('"test"[tiab]')
papers = fetch_details(pmids, max_workers=2, delay=0.3)
print(f"Retrieved {len(papers)} articles")
```

---

### pubmed_supervisor.extraction

#### `extract_info(papers)`

Extract comprehensive author and article information from PubMed records.

**Parameters:**
- `papers` (list): List of PubmedArticle XML objects from `fetch_details()`

**Returns:**
- `list`: List of dicts, one per author per article

**Output Dictionary Keys:**

*Paper Metadata:*
- `pmid` (str): PubMed ID
- `doi` (str or None): Digital Object Identifier
- `pmc_id` (str or None): PubMed Central ID
- `title` (str): Article title
- `journal_title` (str): Journal name
- `journal_iso` (str): ISO journal abbreviation
- `journal_issn` (str): Journal ISSN
- `journal_volume` (str): Volume number
- `journal_issue` (str): Issue number
- `pub_year`, `pub_month`, `pub_day` (str): Publication date components
- `publication_types` (list): Article types (e.g., ['Journal Article', 'Research Support'])
- `language` (str): Publication language code
- `publication_status` (str): Status (e.g., 'Published')

*Author Details:*
- `author` (str): Full author name
- `last_name` (str): Family name
- `fore_name` (str): Given name
- `initials` (str): Author initials
- `author_role` (str): Role description if available
- `valid_yn` (str): Validation flag

*Affiliation Information:*
- `affiliations` (list): List of affiliation strings
- `affiliation_identifiers` (list): ORCID/ROR identifiers if available
- `email` (str or None): Extracted from affiliation text

*Article Classification:*
- `mesh_headings` (list): List of dicts with `descriptor`, `descriptor_ui`, `qualifier`, `qualifier_ui`
- `keywords` (list): Keyword strings
- `grants` (list): List of dicts with `grant_id`, `agency`, `country`

**Example:**
```python
from pubmed_supervisor import fetch_details, extract_info
import pandas as pd

papers = fetch_details(pmids)
rows = extract_info(papers)
df = pd.DataFrame(rows)
print(f"Extracted {len(df)} author records")
```

---

### pubmed_supervisor.enrichment

#### `merge_with_scimago(df, scimago_file='scimagojr_2025.csv')`

Merge author dataframe with SCImago journal quality rankings.

**Parameters:**
- `df` (pandas.DataFrame): Author dataframe with `journal_issn` column
- `scimago_file` (str, optional): Path to SCImago CSV file
  - Default: `'scimagojr_2025.csv'`

**Returns:**
- `pandas.DataFrame`: Enhanced dataframe with SCImago columns

**New Columns Added:**
- `scimago_rank` (int): Journal ranking (1 = top)
- `scimago_sjr` (float): SCImago Journal Rank score
- `scimago_sjr_quartile` (str): Quartile (Q1, Q2, Q3, Q4)
- `scimago_title` (str): Journal title from SCImago
- `scimago_issn` (str): Journal ISSN from SCImago
- `scimago_country` (str): Country of journal publisher
- `scimago_categories` (str): Research categories
- `scimago_h_index` (int): H-index
- `scimago_citations_per_doc_2yr` (float): Citations per document (2 years)
- And more...

**Example:**
```python
from pubmed_supervisor import extract_info, merge_with_scimago
import pandas as pd

df = pd.DataFrame(extract_info(papers))
df = merge_with_scimago(df, scimago_file='scimagojr_2025.csv')
print(df[['journal_title', 'scimago_rank', 'scimago_sjr']].head())
```

---

#### `extract_country(affiliations)`

Extract country name from affiliation text using regex patterns.

**Parameters:**
- `affiliations` (str, list, or None): Single string, list of strings, or None

**Returns:**
- `str`: Country name (e.g., "United States", "Germany") or "Other"

**Supported Countries:** 60+ countries including:
- North America: USA, Canada, Mexico
- Europe: UK, Germany, France, Italy, etc.
- Asia: China, Japan, India, Singapore, Korea, etc.
- Oceania: Australia, New Zealand
- South America: Brazil, Argentina, Chile, etc.
- Africa: South Africa, Egypt, Nigeria, etc.
- Middle East: Israel, Saudi Arabia, etc.

**Matching:**
- Case-insensitive
- Uses regex patterns for flexibility
- Returns first matching country found
- Returns "Other" if no match found

**Example:**
```python
from pubmed_supervisor import extract_country

country = extract_country("Department of CS, MIT, Cambridge, USA")
# Returns: "United States"

countries = extract_country(["Tokyo", "Japan"])
# Returns: "Japan"
```

---

#### `unify_authors(df)`

Aggregate author records (one per article) into unified view (one per author).

**Parameters:**
- `df` (pandas.DataFrame): Author dataframe with columns:
  - `author`, `title`, `affiliations`, `email`, `country`, `journal_title`, `pmid`

**Returns:**
- `pandas.DataFrame`: Unified author view with columns:
  - `author` (str): Author name
  - `email` (str or None): First valid email found
  - `country` (str or None): First valid country found
  - `all_affiliations` (list): Unique affiliation strings
  - `papers` (list): Unique paper titles
  - `journals` (list): Unique journal titles
  - `num_papers` (int): Count of unique papers

**Behavior:**
- One row per unique author
- Rows sorted by `num_papers` (descending)
- Deduplicates affiliations and papers
- Aggregates emails and countries (takes first valid value)

**Example:**
```python
from pubmed_supervisor import extract_info, unify_authors
import pandas as pd

df = pd.DataFrame(extract_info(papers))  # Many rows per author
df_unified = unify_authors(df)  # One row per author

print(df_unified[['author', 'num_papers', 'country']].head())
```

---

### pubmed_supervisor.doi_lookup

#### `find_corresponding_author_from_doi(doi, pubmed_authors=None)`

Extract corresponding author information from article via DOI.

**Parameters:**
- `doi` (str or None): DOI identifier (e.g., `"10.1234/example"`)
- `pubmed_authors` (list, optional): List of author names from PubMed for name matching
  - Used to normalize names from DOI to match PubMed format

**Returns:**
- `list` or `None`: List of dicts with `name` and `email` keys, or None if not found

**Output Structure:**
```python
[
    {
        'name': 'John Smith',      # Author name or None
        'email': 'john@example.com'  # Email address
    },
    ...
]
```

**Data Sources (priority order):**
1. Meta tags (`citation_author_email`, `citation_author`)
2. JSON-LD schema (`mainEntity.author`)
3. Fallback: Email regex pattern search in page text

**Example:**
```python
from pubmed_supervisor import find_corresponding_author_from_doi

corr_authors = find_corresponding_author_from_doi("10.1234/example")
if corr_authors:
    for author in corr_authors:
        print(f"{author['name']}: {author['email']}")
```

---

### pubmed_supervisor.utils

#### `first_valid(series)`

Get the first non-null, non-empty value from a pandas Series.

**Parameters:**
- `series` (pandas.Series): Series to search

**Returns:**
- Value of first non-null, non-empty element, or None

**Example:**
```python
import pandas as pd
from pubmed_supervisor.utils import first_valid

s = pd.Series([None, "", "value", "other"])
result = first_valid(s)  # Returns: "value"
```

---

## Configuration

### pubmed_supervisor.config

Module-level configuration variables:

```python
# PubMed API
ENTREZ_EMAIL = os.getenv("ENTREZ_EMAIL", "your.email@example.com")

# Requests
REQUEST_TIMEOUT = 15  # Seconds
RATE_LIMIT_DELAY = 0.1  # Seconds between requests
MAX_RETRIES = 3  # Retry attempts

# Threading
DEFAULT_WORKERS = 4  # Parallel workers

# Data
SCIMAGO_FILE = "scimagojr_2025.csv"
```

---

## Workflow Example

```python
from pubmed_supervisor import (
    search_pubmed, fetch_details, extract_info,
    merge_with_scimago, extract_country, unify_authors
)
import pandas as pd

# 1. Search
pmids = search_pubmed('("ai"[tiab] OR "ml"[tiab])', mindate='2024/01/01', maxdate='2024/12/31')

# 2. Fetch
papers = fetch_details(pmids[:100], max_workers=4)

# 3. Extract
df = pd.DataFrame(extract_info(papers))

# 4. Enrich
df = merge_with_scimago(df)
df['country'] = df['affiliations'].apply(extract_country)

# 5. Filter & unify
df_filtered = df[(df['email'].notna()) & (df['scimago_rank'] < 1000)]
df_unified = unify_authors(df_filtered)

# 6. Results
print(df_unified[['author', 'email', 'num_papers']].head(20))
```

---

## Error Handling

Common exceptions and solutions:

| Error | Cause | Solution |
|-------|-------|----------|
| `HTTPError 400: Bad Request` | Invalid search query | Check PubMed query syntax |
| `HTTPError 429: Too Many Requests` | Rate limit exceeded | Increase `delay` parameter |
| `ENTREZ_EMAIL not set` | Missing email config | Set `ENTREZ_EMAIL` environment variable |
| `FileNotFoundError` | Missing SCImago file | Download from ScimagoJR website |
| `KeyError` | Unexpected XML structure | May occur with malformed records, caught and handled |

---

## See Also

- [SETUP.md](SETUP.md) - Installation and configuration
- [USAGE.md](USAGE.md) - Common workflows and examples
- [README.md](../README.md) - Project overview
- [examples/](../examples/) - Full working examples
