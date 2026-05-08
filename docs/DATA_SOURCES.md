# Data Sources

Information about data sources used by supervisor-finder.

## PubMed (NCBI)

### Overview
- **Provider**: National Center for Biotechnology Information (NCBI)
- **URL**: https://www.ncbi.nlm.nih.gov/pubmed/
- **Coverage**: >35 million biomedical articles
- **Access**: Free via Entrez API
- **Terms**: See [NCBI Terms and Conditions](https://www.ncbi.nlm.nih.gov/home/about/policies/)

### What We Get
- Article metadata (title, authors, journal, date)
- Author information (names, affiliations, emails)
- MeSH headings and keywords
- Grant information
- DOI and PubMed Central IDs
- Abstract text (not extracted by default)
- Publication types and dates

### How to Use

#### Basic Search
```python
from pubmed_supervisor import search_pubmed

# Simple text search
pmids = search_pubmed('"deep learning"[tiab]')

# Advanced query with MeSH terms
query = '''
("deep learning"[tiab] OR "neural network"[tiab])
AND ("2024"[pdat])
AND NOT ("review"[pt])
'''
pmids = search_pubmed(query)
```

#### Query Syntax
- `[tiab]` - Title/abstract
- `[pt]` - Publication type
- `[pdat]` - Publication date
- `[au]` - Author
- `[ad]` - Affiliation/address
- `[mh]` - MeSH heading

See [NCBI PubMed Help](https://pubmed.ncbi.nlm.nih.gov/help/) for complete syntax.

### Rate Limiting and Policies

**Important**: The NCBI asks users to:
1. **Set your email**: Required for all Entrez API calls
2. **Respect rate limits**: ≤3 requests/second (we use 0.1-0.3s delays)
3. **Cache results**: Don't re-query the same searches
4. **Use responsibly**: Don't automate massive downloads

Our package respects these guidelines with built-in delays and retry logic.

### Free vs. Paid
PubMed access is **completely free** with no authentication required (just your email).

## SCImago Journal Rankings (ScimagoJR)

### Overview
- **Provider**: SCImago (Consejo Superior de Investigaciones Científicas, Spain)
- **URL**: https://www.scimagojr.com/
- **Coverage**: ~43,000 journals
- **Access**: Free download (CSV format)
- **Update Frequency**: Annual
- **Terms**: [Data availability](https://www.scimagojr.com/datadesc.php)

### What We Get
- Journal rankings (overall and by subject area)
- SCImago Journal Rank (SJR) - quality metric
- H-index - productivity and impact metric
- Quartile (Q1-Q4) - comparative ranking
- Citation metrics
- Journal categories and research areas
- Country of publication
- ISSN for matching with articles

### How to Use

1. **Download Data**
   - Visit https://www.scimagojr.com/journalrank.php
   - Select "Download" → CSV format
   - Save as `scimagojr_2025.csv` in your working directory

2. **In Your Code**
   ```python
   from pubmed_supervisor import merge_with_scimago
   import pandas as pd
   
   df = pd.DataFrame(extract_info(papers))
   df = merge_with_scimago(df, scimago_file='scimagojr_2025.csv')
   
   # Now you can filter by:
   print(df['scimago_rank'].min())  # Best ranked journal
   print(df['scimago_sjr'].max())   # Highest SJR
   print(df['scimago_sjr_quartile'].unique())  # Quartiles found
   ```

### Understanding Metrics

**SJR (SCImago Journal Rank)**
- Measures journal prestige
- Higher = more prestigious
- Normalized by subject area
- Range: 0 to ~10+

**Quartile (Q1-Q4)**
- Q1: Top 25% in category
- Q2: 25-50%
- Q3: 50-75%
- Q4: Bottom 25%

**H-Index**
- Number of papers with ≥H citations
- Reflects cumulative impact over time

### Note on Usage
- The data is provided by SCImago for academic use
- Always verify you're using the correct year's data
- Rankings can vary year-to-year
- Some journals may not be in SCImago rankings

## Digital Object Identifier (DOI)

### Overview
- **Provider**: International DOI Foundation
- **URL**: https://www.doi.org/
- **Resolution**: All articles have unique DOIs
- **Access**: Free

### How We Use It
When available, we use DOIs to:
1. Link to article pages
2. Attempt to extract corresponding author information via web scraping
3. Verify article metadata

### Example
```python
from pubmed_supervisor import find_corresponding_author_from_doi

doi = "10.1234/example"
corr_authors = find_corresponding_author_from_doi(doi)
```

## Data Quality Notes

### Author Emails
- **Availability**: ~5-20% of articles have corresponding author emails in metadata
- **Sources**: Affiliation text, meta tags, JSON-LD schema
- **Accuracy**: Variable - verify before contacting
- **False Positives**: May include institutional emails, not personal addresses

### Affiliations
- **Completeness**: Most authors have affiliation data
- **Accuracy**: As reported by authors at publication time
- **Currency**: May be outdated (especially for older articles)
- **Format**: Varies widely; our country extraction uses regex patterns

### Country Detection
- **Method**: Regex pattern matching on affiliation text
- **Accuracy**: ~85-90% for clear affiliation strings
- **Challenges**: 
  - Abbreviations (USA vs US vs US of A)
  - Multiple affiliations
  - Unknown/ambiguous locations
- **Fallback**: Returns "Other" if no match

### MeSH Headings and Keywords
- **Source**: Assigned by NLM indexers or article authors
- **Completeness**: All indexed articles have MeSH headings
- **Use**: Research area identification, filtering

## Citation and Acknowledgment

If you use data from supervisor-finder in your research:

### Citation Format

**APA:**
> Lastname, F. (2024). supervisor-finder: Find academic supervisors from published articles. Retrieved from https://github.com/yourusername/supervisor-finder

**BibTeX:**
```bibtex
@software{supervisorfinder2024,
  title={supervisor-finder: Find Academic Supervisors from Published Articles},
  author={Your Name},
  year={2024},
  url={https://github.com/yourusername/supervisor-finder}
}
```

### Data Sources to Acknowledge

In your methodology, mention:
- PubMed/NCBI Entrez for article data
- SCImago for journal rankings
- Data collection date and query

**Example:**
> Author and article data were obtained from PubMed (NCBI Entrez API) with journal quality metrics from SCImago Journal Rankings. Searches were conducted on [DATE] using the query: [YOUR QUERY].

## Related Resources

- [NCBI Documentation](https://www.ncbi.nlm.nih.gov/books/NBK25501/)
- [PubMed Query Help](https://pubmed.ncbi.nlm.nih.gov/help/)
- [SCImago Data Description](https://www.scimagojr.com/datadesc.php)
- [DOI Handbook](https://www.doi.org/the-doi-system/978-0-262-51365-5/)

## Limitations and Caveats

1. **Temporal Lag**: PubMed indexing can take weeks after publication
2. **Coverage**: Biomedical focus; limited coverage of other fields
3. **Accuracy**: Author-reported information; may contain errors
4. **Completeness**: Not all papers have full metadata
5. **Currency**: Affiliations change; contact info may be outdated
6. **Bias**: Journal coverage in PubMed has geographic biases

## Privacy and Ethics

When using data to contact researchers:
- Always verify information is current
- Respect researchers' privacy
- Follow institutional guidelines
- Be professional and respectful in outreach
- Comply with applicable laws and regulations (GDPR, etc.)

## Future Data Sources

Potential additional sources for future versions:
- ORCID API (researcher profiles)
- ResearchGate/Academia.edu (direct contact)
- arXiv (preprints)
- Google Scholar (citations)
- Institution APIs (researcher directories)

---

**Last Updated:** May 2024  
**Data Sources Version:** 1.0
