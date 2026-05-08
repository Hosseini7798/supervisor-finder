# supervisor-finder

A Python tool for finding potential academic supervisors from published articles via PubMed. Search for articles in your research domain, extract author information, filter by country and journal quality, and identify active researchers for supervision opportunities.

**Features:**
- 🔍 **Smart PubMed Search**: Recursive date-range splitting to handle large result sets (>10,000 articles)
- 📄 **Comprehensive Extraction**: Extracts author details, affiliations, emails, journal info, and more
- 🌍 **Country-Based Filtering**: Identify researchers from target countries/regions
- ⭐ **Journal Quality Metrics**: Merge with SCImago rankings to prioritize high-quality publications
- 👥 **Author Unification**: Aggregate author information across multiple papers
- 📧 **Email Extraction**: Attempts to find corresponding author emails via DOI lookup
- ⚡ **Parallel Processing**: Multi-threaded fetching for speed
- 📊 **Export Results**: Results as pandas DataFrames for further analysis

## Quick Start

### 1. Installation

```bash
pip install -e .
```

Or install from requirements:
```bash
pip install -r requirements.txt
```

### 2. Set Your Email (Required for PubMed)

The NCBI Entrez API requires an email address. Set it in one of these ways:

```bash
# Option A: Environment variable
export ENTREZ_EMAIL="your.email@example.com"

# Option B: Create .env file (add to .gitignore)
echo 'ENTREZ_EMAIL=your.email@example.com' > .env

# Option C: Update config directly (not recommended for production)
# src/pubmed_supervisor/config.py
```

### 3. Download SCImago Data

Download the ScimagoJR 2025 journal rankings:
1. Visit https://www.scimagojr.com/journalrank.php
2. Download the CSV file
3. Place in your working directory as `scimagojr_2025.csv`

### 4. Run a Basic Example

```python
from pubmed_supervisor import search_pubmed, fetch_details, extract_info, merge_with_scimago, extract_country, unify_authors
import pandas as pd

# Search PubMed
query = '("deep learning"[tiab] OR "machine learning"[tiab]) AND ("medical imaging"[tiab])'
pmids = search_pubmed(query, mindate='2023/01/01', maxdate='2024/12/31')

# Fetch article details
papers = fetch_details(pmids, max_workers=4, delay=0.2)

# Extract author information
author_rows = extract_info(papers)
df = pd.DataFrame(author_rows)

# Enrich with SCImago data
df = merge_with_scimago(df, scimago_file='scimagojr_2025.csv')

# Extract countries
df['country'] = df['affiliations'].apply(extract_country)

# Filter by criteria
selected_countries = ['Canada', 'United Kingdom', 'Germany', 'Switzerland']
df_filtered = df[
    (df['email'].notna()) & 
    (df['country'].isin(selected_countries)) &
    (df['scimago_rank'] < 1000)
]

# Unify authors (one row per unique author)
df_unified = unify_authors(df_filtered)
print(df_unified[['author', 'email', 'country', 'num_papers']].head(20))
```

See [examples/](examples/) for more detailed examples.

## API Overview

### Core Functions

#### `search_pubmed(query, mindate, maxdate)`
Search PubMed with automatic date-range splitting for large result sets.

**Parameters:**
- `query` (str): PubMed search query with MeSH/text qualifiers
- `mindate` (str): Start date (YYYY/MM/DD format)
- `maxdate` (str): End date (YYYY/MM/DD format)

**Returns:** List of PMIDs (strings)

#### `fetch_details(pmids, max_workers, delay, max_retries)`
Fetch full article XML records in parallel with retry logic.

**Parameters:**
- `pmids` (list): List of PubMed IDs
- `max_workers` (int): Number of parallel threads
- `delay` (float): Seconds between requests (respects NCBI policy)
- `max_retries` (int): Retry attempts on failure

**Returns:** List of PubmedArticle XML objects

#### `extract_info(papers)`
Extract author, article, and metadata from PubMed XML records.

**Returns:** List of dicts (one row per author per article)

#### `merge_with_scimago(df, scimago_file)`
Merge author DataFrame with SCImago journal rankings by ISSN.

**Returns:** Enriched DataFrame with journal quality metrics

#### `extract_country(affiliations)`
Extract country from affiliation text using regex patterns.

**Returns:** Country name (str) or "Other"

#### `unify_authors(df)`
Aggregate author records into one row per unique author.

**Returns:** Unified author DataFrame sorted by publication count

See [docs/API.md](docs/API.md) for full API reference.

## Data Structure

### Author Extraction Output

Each row contains:

**Paper Metadata:**
- `pmid`, `doi`, `pmc_id`, `title`, `journal_title`, `journal_iso`, `journal_issn`
- `journal_volume`, `journal_issue`, `pub_year`, `pub_month`, `pub_day`
- `publication_types`, `language`, `publication_status`

**Author Details:**
- `author`, `last_name`, `fore_name`, `initials`
- `author_role`, `valid_yn`

**Affiliation Information:**
- `affiliations` (list), `affiliation_identifiers` (list), `email`

**Article Classification:**
- `mesh_headings` (list of dicts), `keywords` (list)
- `grants` (list of dicts with grant_id, agency, country)

**SCImago Enrichment** (after merge):
- `scimago_rank`, `scimago_sjr`, `scimago_sjr_quartile`, `scimago_title`
- `scimago_country`, `scimago_categories`, `scimago_h_index`, etc.

## Examples

### Example 1: Find AI Researchers

```python
query = '''("artificial intelligence"[tiab] OR "machine learning"[tiab] OR 
            "deep learning"[tiab]) AND ("2024"[pdat])'''
pmids = search_pubmed(query)
papers = fetch_details(pmids[:100])  # Limit for demo
df = pd.DataFrame(extract_info(papers))
df = merge_with_scimago(df)
df['country'] = df['affiliations'].apply(extract_country)

# Find top authors
top_authors = unify_authors(df[df['scimago_rank'] < 500])
print(top_authors[['author', 'country', 'num_papers', 'email']].head(10))
```

### Example 2: Targeted Country Search

```python
target_countries = ['Canada', 'Japan', 'Switzerland']
df_country = df[df['country'].isin(target_countries)]
df_unified = unify_authors(df_country[df_country['email'].notna()])
print(df_unified[['author', 'email', 'num_papers']])
```

See [examples/](examples/) for more use cases.

## Documentation

- [SETUP.md](docs/SETUP.md) - Detailed setup instructions
- [USAGE.md](docs/USAGE.md) - Comprehensive usage guide
- [API.md](docs/API.md) - Full API reference
- [DATA_SOURCES.md](docs/DATA_SOURCES.md) - Information on data sources

## PubMed Query Tips

Use PubMed's query syntax for precision:

- `"text"[tiab]` - Text words in title or abstract
- `"phrase"[tiab]` - Exact phrase in title/abstract
- `term1 OR term2` - Either term
- `term1 AND term2` - Both terms
- `"publication type"[pt]` - Filter by publication type
- `"date"[pdat]` - Publication date

**Example Queries:**
```
("neural network"[tiab] OR "deep learning"[tiab]) AND ("medical imaging"[tiab])
("machine learning"[tiab] OR "artificial intelligence"[tiab]) NOT "review"[pt]
("image segmentation"[tiab]) AND ("2023"[pdat] OR "2024"[pdat])
```

See [NCBI PubMed Help](https://pubmed.ncbi.nlm.nih.gov/help/) for more.

## Limitations & Notes

- **PubMed Rate Limits**: Respects NCBI guidelines with 0.1-0.3s delays between requests
- **Email Extraction**: Not all papers include corresponding author emails
- **Country Detection**: Based on regex patterns; may miss edge cases
- **SCImago Data**: Requires manual download from official ScimagoJR website
- **Large Datasets**: Processing 10,000+ articles may take significant time

## Citation

If you use supervisor-finder in research, please cite:

```bibtex
@software{supervisorfinder2024,
  title={supervisor-finder: Find Academic Supervisors from Published Articles},
  author={Your Name},
  year={2024},
  url={https://github.com/yourusername/supervisor-finder}
}
```

## Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

This project is licensed under the MIT License - see [LICENSE](LICENSE) for details.

## Disclaimer

This tool is for educational and research purposes. Users are responsible for:
- Complying with NCBI's Terms and Conditions
- Respecting rate limits and responsible API usage
- Verifying information before contacting potential supervisors
- Following institutional guidelines and regulations

## Support

- 📖 See [docs/](docs/) for detailed documentation
- 🐛 Report bugs via GitHub Issues
- 💡 Suggest features via GitHub Discussions
- 📧 Contact: [your.email@example.com]

---

**Last Updated:** May 2024  
**Version:** 0.1.0 (Alpha)
