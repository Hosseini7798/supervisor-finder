"""
Example 2: Custom Filtering

This example shows advanced filtering techniques:
- Filter by journal impact (SJR score)
- Filter by research categories
- Find corresponding authors via DOI
- Export results in multiple formats
"""

import pandas as pd
from pubmed_supervisor import (
    search_pubmed,
    fetch_details,
    extract_info,
    merge_with_scimago,
    extract_country,
    unify_authors,
    find_corresponding_author_from_doi,
)

# ============================================================================
# Search and Extract
# ============================================================================

print("Searching PubMed...")
query = '("computer vision"[tiab] OR "image segmentation"[tiab]) AND ("2024"[pdat])'
pmids = search_pubmed(query, mindate="2024/01/01", maxdate="2024/12/31")

print(f"Fetching {min(50, len(pmids))} articles...")
papers = fetch_details(pmids[:50], max_workers=2)

print("Extracting information...")
df = pd.DataFrame(extract_info(papers))
df = merge_with_scimago(df, scimago_file="data/sample/scimagojr_2025_sample.csv")
df["country"] = df["affiliations"].apply(extract_country)

# ============================================================================
# ADVANCED FILTERING: Example 1 - High-Impact Journals
# ============================================================================

print("\n" + "=" * 80)
print("Filter 1: High-Impact Journals (Top 500 by SCImago Rank)")
print("=" * 80)

df_high_impact = df[df["scimago_rank"] < 500]
print(f"Found {len(df_high_impact)} records from {df_high_impact['author'].nunique()} unique authors")

# Show statistics
print(f"\nTop journals by publication count in filtered set:")
print(df_high_impact["journal_title"].value_counts().head(5))

# ============================================================================
# ADVANCED FILTERING: Example 2 - Geographic Targeting
# ============================================================================

print("\n" + "=" * 80)
print("Filter 2: Europe + Developed Asian Countries (with email)")
print("=" * 80)

europe_asia = [
    "United Kingdom",
    "Germany",
    "France",
    "Italy",
    "Netherlands",
    "Switzerland",
    "Sweden",
    "Denmark",
    "Japan",
    "South Korea",
    "Singapore",
]

df_region = df[(df["country"].isin(europe_asia)) & (df["email"].notna())]
print(f"Found {len(df_region)} records from {df_region['author'].nunique()} unique authors")

# Geographic distribution
print(f"\nGeographic distribution:")
print(df_region["country"].value_counts())

# ============================================================================
# ADVANCED FILTERING: Example 3 - Multi-criteria Selection
# ============================================================================

print("\n" + "=" * 80)
print("Filter 3: Multi-Criteria (High Impact + US/Canada + Recent)")
print("=" * 80)

north_america = ["United States", "Canada"]

df_multi = df[
    (df["scimago_rank"] < 1000)
    & (df["scimago_sjr"].notna())
    & (df["country"].isin(north_america))
    & (df["email"].notna())
    & (df["pub_year"].astype(str) == "2024")
]

print(f"Found {len(df_multi)} records from {df_multi['author'].nunique()} unique authors")

if len(df_multi) > 0:
    print(f"\nAverage journal rank: {df_multi['scimago_rank'].mean():.0f}")
    print(f"Average SJR score: {df_multi['scimago_sjr'].mean():.2f}")

# ============================================================================
# UNIFY AND DISPLAY
# ============================================================================

print("\n" + "=" * 80)
print("Unified Authors (All Filters Combined)")
print("=" * 80)

df_all_filtered = df[
    (df["email"].notna())
    & (df["scimago_rank"] < 1500)
    & (df["country"].notna())
    & (df["country"] != "Other")
]

df_unified = unify_authors(df_all_filtered)

print(f"\nTotal unified authors: {len(df_unified)}")
print("\nTop 15 Authors by Publication Count:")
display_df = df_unified[["author", "country", "email", "num_papers"]].head(15)
print(display_df.to_string())

# ============================================================================
# EXPORT RESULTS
# ============================================================================

print("\n" + "=" * 80)
print("Export Results")
print("=" * 80)

# Export 1: Detailed records
df_all_filtered.to_csv("detailed_authors.csv", index=False)
print("✓ Exported detailed records: detailed_authors.csv")

# Export 2: Unified authors
df_unified.to_csv("unified_authors.csv", index=False)
print("✓ Exported unified authors: unified_authors.csv")

# Export 3: Contact list (name and email only)
contact_list = df_unified[["author", "email", "country"]].copy()
contact_list = contact_list[contact_list["email"].notna()]
contact_list.to_csv("contact_list.csv", index=False)
print(f"✓ Exported contact list: contact_list.csv ({len(contact_list)} contacts)")

# ============================================================================
# BONUS: Attempt to Extract Corresponding Authors via DOI
# ============================================================================

print("\n" + "=" * 80)
print("BONUS: Extract Corresponding Authors via DOI (First 5)")
print("=" * 80)

articles_with_doi = df_all_filtered[df_all_filtered["doi"].notna()].drop_duplicates(
    "pmid"
)

for idx, (_, row) in enumerate(articles_with_doi.head(5).iterrows()):
    doi = row["doi"]
    print(f"\n{idx + 1}. DOI: {doi}")
    print(f"   Title: {row['title'][:60]}...")

    # Try to find corresponding author
    corr_authors = find_corresponding_author_from_doi(doi)
    if corr_authors:
        for corr in corr_authors:
            print(f"   → Corresponding author: {corr['name']} ({corr['email']})")
    else:
        print(f"   → No corresponding author found via DOI")

print("\n✓ Custom filtering examples complete!")
