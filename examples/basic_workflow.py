"""
Example 1: Basic Workflow

A complete end-to-end example showing how to:
1. Search PubMed for articles
2. Fetch full article records
3. Extract author information
4. Enrich with SCImago data
5. Filter results
6. Unify author records
"""

import pandas as pd
from pubmed_supervisor import (
    search_pubmed,
    fetch_details,
    extract_info,
    merge_with_scimago,
    extract_country,
    unify_authors,
)

# ============================================================================
# STEP 1: Search PubMed
# ============================================================================

print("\n" + "=" * 80)
print("STEP 1: Search PubMed")
print("=" * 80)

# Define your search query using PubMed query syntax
query = '''
("artificial intelligence"[tiab] OR "machine learning"[tiab] OR "deep learning"[tiab])
AND ("medical imaging"[tiab] OR "image analysis"[tiab])
AND ("2024"[pdat])
'''

# Search with date range (splits automatically if >10,000 results)
pmids = search_pubmed(query, mindate="2024/01/01", maxdate="2024/12/31")
print(f"Found {len(pmids)} articles")

# ============================================================================
# STEP 2: Fetch Full Article Details
# ============================================================================

print("\n" + "=" * 80)
print("STEP 2: Fetch Article Details")
print("=" * 80)

# Fetch up to first 100 articles for demo (remove [:100] for all)
papers = fetch_details(pmids[:100], max_workers=4, delay=0.2)

# ============================================================================
# STEP 3: Extract Author Information
# ============================================================================

print("\n" + "=" * 80)
print("STEP 3: Extract Author Information")
print("=" * 80)

# Extract comprehensive author and article information
author_rows = extract_info(papers)
df = pd.DataFrame(author_rows)
print(f"Extracted {len(df)} author records from {len(papers)} articles")
print(f"\nDataFrame shape: {df.shape}")
print(f"Columns: {list(df.columns[:10])}...")  # Show first 10 columns

# ============================================================================
# STEP 4: Enrich with SCImago Data
# ============================================================================

print("\n" + "=" * 80)
print("STEP 4: Merge with SCImago Journal Rankings")
print("=" * 80)

# Merge with journal quality metrics
# NOTE: Requires scimagojr_2025.csv file
df = merge_with_scimago(df, scimago_file="data/sample/scimagojr_2025_sample.csv")
print(f"Merged with SCImago. Unique journals: {df['journal_title'].nunique()}")

# ============================================================================
# STEP 5: Extract Country Information
# ============================================================================

print("\n" + "=" * 80)
print("STEP 5: Extract Country from Affiliations")
print("=" * 80)

df["country"] = df["affiliations"].apply(extract_country)
print(f"Countries found: {df['country'].nunique()}")
print(df["country"].value_counts().head(10))

# ============================================================================
# STEP 6: Filter Results
# ============================================================================

print("\n" + "=" * 80)
print("STEP 6: Filter by Criteria")
print("=" * 80)

# Select target countries
selected_countries = [
    "Canada",
    "United Kingdom",
    "Germany",
    "France",
    "Netherlands",
    "Switzerland",
    "Sweden",
    "Japan",
]

# Filter: has email, target country, good journal ranking
df_filtered = df[
    (df["email"].notna())
    & (df["country"].isin(selected_countries))
    & (df["scimago_rank"] < 1000)
]

print(f"Filtered to {len(df_filtered)} records")
print(f"From {df_filtered['author'].nunique()} unique authors")
print(f"In {len(selected_countries)} target countries")

# ============================================================================
# STEP 7: Unify Authors
# ============================================================================

print("\n" + "=" * 80)
print("STEP 7: Unify Authors (Aggregate Across Articles)")
print("=" * 80)

# Create unified view: one row per author
df_unified = unify_authors(df_filtered)

print(f"Unified to {len(df_unified)} unique authors")
print(f"\nTop 10 Most Prolific Authors:")
print(df_unified[["author", "country", "email", "num_papers"]].head(10).to_string())

# ============================================================================
# STEP 8: Save Results
# ============================================================================

print("\n" + "=" * 80)
print("STEP 8: Save Results")
print("=" * 80)

# Save detailed records
df_filtered.to_csv("output_author_detailed.csv", index=False)
print("✓ Saved detailed records: output_author_detailed.csv")

# Save unified author view
df_unified.to_csv("output_authors_unified.csv", index=False)
print("✓ Saved unified authors: output_authors_unified.csv")

# ============================================================================
# SUMMARY
# ============================================================================

print("\n" + "=" * 80)
print("SUMMARY")
print("=" * 80)
print(f"Total articles fetched: {len(papers)}")
print(f"Total author records extracted: {len(df)}")
print(f"After filtering: {len(df_filtered)} records ({df_filtered['author'].nunique()} unique authors)")
print(f"Unified authors: {len(df_unified)} authors")
print(f"\nTop author by publication count:")
top_author = df_unified.iloc[0]
print(f"  Name: {top_author['author']}")
print(f"  Email: {top_author['email']}")
print(f"  Country: {top_author['country']}")
print(f"  Publications: {top_author['num_papers']}")
print("\n✓ Workflow complete! Check output CSV files for results.")
