# Setup Guide

Detailed instructions for setting up supervisor-finder.

## System Requirements

- **Python**: 3.8 or higher
- **Operating System**: Linux, macOS, or Windows
- **Internet**: Required for PubMed API access
- **NCBI Account**: Not required, but email needed for Entrez API

## Installation Steps

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/supervisor-finder.git
cd supervisor-finder
```

### 2. Create Virtual Environment (Recommended)

```bash
# Using venv
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# OR using conda
conda create -n supervisor-finder python=3.9
conda activate supervisor-finder
```

### 3. Install Dependencies

**Option A: Development Installation (recommended for users)**
```bash
pip install -e .
```

**Option B: From requirements.txt**
```bash
pip install -r requirements.txt
```

**Option C: With development tools**
```bash
pip install -e ".[dev]"
```

### 4. Configure PubMed API (NCBI Entrez)

The NCBI Entrez API **requires** your email address. Set it before using the package:

#### Method 1: Environment Variable (Recommended)

```bash
# Add to your shell profile (~/.bashrc, ~/.zshrc, or ~/.bash_profile)
export ENTREZ_EMAIL="your.email@example.com"

# Or set temporarily for current session
export ENTREZ_EMAIL="your.email@example.com"
```

Then verify it's set:
```bash
echo $ENTREZ_EMAIL
```

#### Method 2: Create .env File

```bash
cd supervisor-finder
echo 'ENTREZ_EMAIL=your.email@example.com' > .env
```

Then load in your Python script:
```python
from dotenv import load_dotenv
load_dotenv()  # Loads .env file
```

#### Method 3: Update Configuration Directly

Edit `src/pubmed_supervisor/config.py`:
```python
ENTREZ_EMAIL = "your.email@example.com"
```

### 5. Download SCImago Journal Rankings

The package uses SCImago journal quality metrics. Download the data:

1. Visit https://www.scimagojr.com/journalrank.php
2. Click "Download data" (CSV format)
3. Place the file in your working directory as `scimagojr_2025.csv`

Alternatively, download from command line:
```bash
# Using curl or wget
curl -o scimagojr_2025.csv "https://www.scimagojr.com/journalrank.php?out=xls"
```

Or use a Python script:
```python
import requests
import pandas as pd

# Note: ScimagoJR may require manual download from their website
# as they have anti-scraping measures
```

## Verification

Test your installation:

```bash
python -c "import pubmed_supervisor; print('✓ Installation successful')"
```

Or run a quick test:

```python
from pubmed_supervisor import search_pubmed

# This requires ENTREZ_EMAIL to be set
pmids = search_pubmed('"test"[tiab]', mindate='2024/01/01', maxdate='2024/01/02')
print(f"Found {len(pmids)} test results")
```

## Configuration Reference

### Environment Variables

| Variable | Required | Default | Example |
|----------|----------|---------|---------|
| `ENTREZ_EMAIL` | Yes | None | `user@example.com` |
| `SCIMAGO_FILE` | No | `scimagojr_2025.csv` | `/data/journals.csv` |

### Configuration File

Edit `src/pubmed_supervisor/config.py`:

```python
# PubMed API
ENTREZ_EMAIL = "your.email@example.com"

# Request settings
REQUEST_TIMEOUT = 15  # Seconds
RATE_LIMIT_DELAY = 0.1  # Seconds between requests
MAX_RETRIES = 3  # Retry attempts on failure

# Threading
DEFAULT_WORKERS = 4  # Parallel fetching threads

# Data files
SCIMAGO_FILE = "scimagojr_2025.csv"  # SCImago data path
```

## Troubleshooting

### Issue: "ENTREZ_EMAIL not set"

**Solution**: Set the environment variable:
```bash
export ENTREZ_EMAIL="your.email@example.com"
python your_script.py
```

### Issue: "HTTPError 429: Too Many Requests"

**Solution**: You're hitting NCBI rate limits. The package has retry logic, but if it persists:
- Increase the `delay` parameter in `fetch_details()`
- Reduce the number of `max_workers`
- Wait a few hours before retrying

Example:
```python
papers = fetch_details(pmids, max_workers=2, delay=0.5)
```

### Issue: "scimagojr_2025.csv not found"

**Solution**: Download the file from https://www.scimagojr.com/journalrank.php and place in your working directory.

Or specify the path:
```python
df = merge_with_scimago(df, scimago_file='/path/to/scimagojr_2025.csv')
```

### Issue: "ImportError: No module named 'Bio'"

**Solution**: Install Biopython:
```bash
pip install biopython
```

### Issue: Memory issues with large datasets

**Solution**: Process in batches:
```python
# Process 100 articles at a time
batch_size = 100
for i in range(0, len(pmids), batch_size):
    batch_pmids = pmids[i:i+batch_size]
    papers = fetch_details(batch_pmids)
    df_batch = pd.DataFrame(extract_info(papers))
    # Process batch...
```

## Performance Tuning

### For Speed

```python
# Increase workers for parallel fetching
papers = fetch_details(pmids, max_workers=8, delay=0.05)
```

### For Stability

```python
# Decrease workers and increase delay
papers = fetch_details(pmids, max_workers=2, delay=0.5)
```

### For Memory

```python
# Process in smaller chunks
batch_pmids = pmids[0:1000]  # 1000 at a time
papers = fetch_details(batch_pmids, max_workers=4)
```

## Next Steps

1. Read the [USAGE.md](USAGE.md) guide for common workflows
2. Review [examples/](../examples/) for code samples
3. Check [API.md](API.md) for detailed function documentation
4. See [DATA_SOURCES.md](DATA_SOURCES.md) for information about data sources

## Support

- 📖 Documentation: See [docs/](.)
- 🐛 Issues: https://github.com/yourusername/supervisor-finder/issues
- 📧 Contact: your.email@example.com

## NCBI Policies

When using the NCBI Entrez API:

- ✅ Always provide your email address
- ✅ Respect rate limits (package has delays built-in)
- ✅ Use the API responsibly
- ✅ Cache results when possible
- ❌ Don't automate excessive downloads
- ❌ Don't abuse the service

See [NCBI's Use Policies](https://www.ncbi.nlm.nih.gov/home/develop/api/)

---

**Need help?** Open an issue on GitHub or see [README.md](../README.md#support)
