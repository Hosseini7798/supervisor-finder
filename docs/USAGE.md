# Usage Guide

Common workflows and usage patterns for supervisor-finder.

## Table of Contents

1. [Basic Workflow](#basic-workflow)
2. [Filtering Techniques](#filtering-techniques)
3. [Batch Processing](#batch-processing)
4. [Working with Results](#working-with-results)
5. [Advanced Use Cases](#advanced-use-cases)

## Basic Workflow

### Complete End-to-End Example

```python
from pubmed_supervisor import (
    search_pubmed, fetch_details, extract_info,
    merge_with_scimago, extract_country, unify_authors
)
import pandas as pd

# 1. Define your search query
query = '''
("deep learning"[tiab] OR "neural network"[tiab])
AND ("image analysis"[tiab] OR "computer vision"[tiab])
AND ("2024"[pdat])
'''

# 2. Search PubMed (automatically handles large result sets)
print("Searching PubMed...")
pmids = search_pubmed(query, mindate='2024/01/01', maxdate='2024/12/31')
print(f"Found {len(pmids)} articles")

# 3. Fetch full article details
print(f"Fetching details for {len(pmids)} articles...")
papers = fetch_details(pmids, max_workers=4, delay=0.2)

# 4. Extract author and article information
print("Extracting author information...")
rows = extract_info(papers)
df = pd.DataFrame(rows)
print(f"Extracted {len(df)} author records")

# 5. Enrich with journal quality metrics
print("Enriching with SCImago data...")
df = merge_with_scimago(df, scimago_file='scimagojr_2025.csv')

# 6. Extract countries from affiliations
print("Extracting countries...")
df['country'] = df['affiliations'].apply(extract_country)

# 7. Filter by your criteria
print("Filtering results...")
selected_countries = ['Canada', 'United Kingdom', 'Germany', 'Switzerland']
df_filtered = df[
    (df['email'].notna()) &  # Has email contact
    (df['country'].isin(selected_countries)) &  # Right country
    (df['scimago_rank'] < 1000)  # Good journal
]

# 8. Unify authors (aggregate across papers)
print("Unifying authors...")
df_unified = unify_authors(df_filtered)

# 9. Results!
print(f"\nFound {len(df_unified)} potential supervisors:")
print(df_unified[['author', 'email', 'country', 'num_papers']].head(20))

# 10. Save results
df_unified.to_csv('supervisors.csv', index=False)
print("Results saved to supervisors.csv")
```

## Filtering Techniques

### Filter by Journal Quality (SJR Score)

```python
from pubmed_supervisor import extract_info, merge_with_scimago
import pandas as pd

df = pd.DataFrame(extract_info(papers))
df = merge_with_scimago(df)

# Filter for SJR score > 2.0 (high quality)
df_high_sjr = df[df['scimago_sjr'] > 2.0]

# Filter for top quartile journals (Q1)
df_q1 = df[df['scimago_sjr_quartile'] == 'Q1']

print(f"High-quality journals: {len(df_high_sjr)} records")
print(f"Top quartile journals: {len(df_q1)} records")
```

### Filter by Research Category

```python
# Filter for specific research categories
categories_of_interest = ['Computer Science', 'Mathematics', 'Engineering']

df_categories = df[
    df['scimago_categories'].str.contains(
        '|'.join(categories_of_interest),
        case=False,
        na=False
    )
]

print(f"Found {len(df_categories)} records in target categories")
```

### Geographic Filtering

```python
from pubmed_supervisor import extract_country

# Define regions
europe = ['Germany', 'France', 'UK', 'Netherlands', 'Switzerland']
asia = ['Japan', 'South Korea', 'Singapore', 'China']

# Extract countries
df['country'] = df['affiliations'].apply(extract_country)

# Filter by region
df_europe = df[df['country'].isin(europe)]
df_asia = df[df['country'].isin(asia)]

# Show distribution
print(df['country'].value_counts())
```

### Contact Information Filtering

```python
# Authors with valid email addresses
df_with_email = df[df['email'].notna()]
print(f"{len(df_with_email)} authors have email contact")

# Multiple strategies to find emails
df_detailed = df[df['affiliations'].str.len() > 0]
df_institutional = df[
    df['affiliations'].str.contains('@', na=False)  # Has email-like content
]

print(f"Detailed affiliations: {len(df_detailed)}")
print(f"Potential email contact: {len(df_institutional)}")
```

### Multi-Criteria Filtering

```python
# Complex filtering combining multiple criteria
df_candidates = df[
    # Contact information
    (df['email'].notna()) |
    (df['affiliations'].str.contains('@', na=False)) |
    
    # Journal quality
    (df['scimago_rank'] < 1000) &
    (df['scimago_sjr'] > 1.5) &
    
    # Geographic location
    (df['country'].isin(['US', 'UK', 'Canada', 'Germany'])) &
    
    # Recent publications
    (df['pub_year'] == '2024') &
    
    # Research area (via keywords)
    (df['keywords'].str.len() > 0)
]

print(f"Found {len(df_candidates)} candidates matching all criteria")
```

## Batch Processing

### Process Large Datasets in Chunks

```python
def process_in_batches(pmids, batch_size=100):
    """Process PMIDs in batches to manage memory."""
    all_df = []
    
    for i in range(0, len(pmids), batch_size):
        batch_pmids = pmids[i:i+batch_size]
        print(f"Processing batch {i//batch_size + 1} ({len(batch_pmids)} articles)...")
        
        papers = fetch_details(batch_pmids, max_workers=2)
        df_batch = pd.DataFrame(extract_info(papers))
        df_batch = merge_with_scimago(df_batch)
        
        all_df.append(df_batch)
    
    return pd.concat(all_df, ignore_index=True)

# Usage
pmids = search_pubmed(query, mindate='2024/01/01', maxdate='2024/12/31')
df = process_in_batches(pmids, batch_size=100)
```

### Save Intermediate Results

```python
import json
from pathlib import Path

# Save PMIDs for later use
with open('pmids_cache.json', 'w') as f:
    json.dump(pmids, f)

# Later: Load from cache
with open('pmids_cache.json', 'r') as f:
    pmids = json.load(f)

# Save intermediate DataFrames
df_raw.to_csv('authors_raw.csv', index=False)  # Before filtering
df_filtered.to_csv('authors_filtered.csv', index=False)  # After filtering
df_unified.to_csv('authors_unified.csv', index=False)  # Final results
```

## Working with Results

### Export to Different Formats

```python
import pandas as pd

# CSV (default)
df_unified.to_csv('supervisors.csv', index=False)

# Excel
df_unified.to_excel('supervisors.xlsx', index=False)

# JSON
df_unified.to_json('supervisors.json', orient='records', indent=2)

# Tab-separated values
df_unified.to_csv('supervisors.tsv', sep='\t', index=False)
```

### Create Contact List

```python
# Simple contact export
contact_df = df_unified[['author', 'email', 'country']].copy()
contact_df = contact_df[contact_df['email'].notna()]
contact_df.to_csv('contact_list.csv', index=False)

# With additional info
contact_df = df_unified[[
    'author', 'email', 'country', 'num_papers',
    'all_affiliations', 'journals'
]].copy()
contact_df['affiliation_summary'] = contact_df['all_affiliations'].apply(
    lambda x: '; '.join(x[:2]) if isinstance(x, list) else str(x)
)
contact_df[['author', 'email', 'country', 'num_papers', 'affiliation_summary']].to_csv(
    'contact_detailed.csv', index=False
)
```

### Statistics and Analysis

```python
# Basic statistics
print(f"Total authors: {len(df_unified)}")
print(f"Average papers per author: {df_unified['num_papers'].mean():.1f}")
print(f"Median papers per author: {df_unified['num_papers'].median():.0f}")

# By country
print("\nAuthors by country:")
print(df_unified['country'].value_counts())

# By number of publications
print("\nPublication distribution:")
print(df_unified['num_papers'].describe())

# Top authors
print("\nTop 10 authors by publication count:")
print(df_unified.nlargest(10, 'num_papers')[['author', 'num_papers', 'country']])
```

### Create Research Profile

```python
# Build detailed profile for an author
author_name = "John Smith"
author_data = df[df['author'] == author_name]

profile = {
    'name': author_name,
    'email': author_data['email'].iloc[0] if len(author_data) > 0 else None,
    'publications': author_data['title'].tolist(),
    'journals': author_data['journal_title'].unique().tolist(),
    'keywords': list(set(
        kw for kws in author_data['keywords'] 
        for kw in (kws if isinstance(kws, list) else [kws])
    )),
    'countries': author_data['country'].unique().tolist(),
    'mesh_topics': list(set(
        m['descriptor'] for meshes in author_data['mesh_headings']
        for m in (meshes if isinstance(meshes, list) else [meshes])
    )),
    'num_papers': len(author_data),
}

import json
print(json.dumps(profile, indent=2))
```

## Advanced Use Cases

### Find Co-Authors of Top Researchers

```python
# Find top author
top_author = df_unified.iloc[0]
top_name = top_author['author']

# Find all their papers
top_papers = df[df['author'] == top_name]['pmid'].unique()

# Find co-authors
coauthors = df[df['pmid'].isin(top_papers)]['author'].unique()
coauthors_df = df[df['author'].isin(coauthors)].groupby('author').agg({
    'pmid': 'nunique',
    'email': lambda x: x[x.notna()].iloc[0] if any(x.notna()) else None,
    'country': lambda x: x[x.notna()].iloc[0] if any(x.notna()) else None,
}).reset_index()
coauthors_df.columns = ['author', 'num_papers', 'email', 'country']
coauthors_df = coauthors_df.sort_values('num_papers', ascending=False)

print(f"Found {len(coauthors_df)} co-authors of {top_name}:")
print(coauthors_df.head(10))
```

### Identify Emerging Researchers

```python
# Recent publications with fewer total papers (emerging researchers)
df_recent = df[df['pub_year'] == '2024']
authors_2024 = df_recent.groupby('author')['pmid'].nunique().reset_index()
authors_2024.columns = ['author', 'papers_2024']

# Get total papers
total_papers = df.groupby('author')['pmid'].nunique().reset_index()
total_papers.columns = ['author', 'total_papers']

# Merge
emerging = authors_2024.merge(total_papers, on='author')
emerging = emerging[emerging['total_papers'] < 20]  # Early career
emerging = emerging.sort_values('papers_2024', ascending=False)

print("Emerging researchers (recent, early career):")
print(emerging.head(10))
```

### Track Publication Trends

```python
# Papers per year
papers_per_year = df.groupby('pub_year')['pmid'].nunique()
print("\nPapers per year:")
print(papers_per_year)

# Authors per year
authors_per_year = df.groupby('pub_year')['author'].nunique()
print("\nNew authors per year:")
print(authors_per_year)

# Top journals over time
top_journals = df.groupby(['pub_year', 'journal_title'])['pmid'].nunique().reset_index()
top_journals = top_journals.sort_values('pub_year')
print("\nTop journals by year:")
print(top_journals[top_journals['pmid'] > 5])
```

## Tips and Best Practices

- **Start Small**: Test your query with a small date range first
- **Cache Results**: Save PMIDs and DataFrames to avoid re-fetching
- **Handle Errors**: Wrap API calls in try-except for robustness
- **Rate Limiting**: Respect NCBI policies; use appropriate delays
- **Memory**: Process large datasets in batches
- **Verification**: Always verify emails and affiliations before contacting
- **Data Quality**: Some records may have incomplete information
- **Updates**: Periodically re-run searches for new publications

## See Also

- [API.md](API.md) - Function reference
- [SETUP.md](SETUP.md) - Installation guide
- [examples/](../examples/) - Working examples
- [README.md](../README.md) - Project overview
