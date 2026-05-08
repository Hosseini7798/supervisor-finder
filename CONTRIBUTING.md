# Contributing to supervisor-finder

We welcome contributions! This document provides guidelines for contributing.

## Code of Conduct

- Be respectful and inclusive
- Assume good faith
- Constructive feedback only
- No harassment or discrimination

## How to Contribute

### 1. Report Bugs

Report bugs via [GitHub Issues](https://github.com/yourusername/supervisor-finder/issues)

**Good bug reports include:**
- Clear description of the issue
- Steps to reproduce
- Expected vs. actual behavior
- Python version and OS
- Error traceback/logs
- Minimal reproducible example

### 2. Suggest Features

Share feature ideas via GitHub Issues or Discussions

**Include:**
- Rationale: Why is this needed?
- Use case: Who benefits?
- Example: How would it work?
- Alternatives considered

### 3. Submit Code Changes

#### Setup Development Environment

```bash
git clone https://github.com/yourusername/supervisor-finder.git
cd supervisor-finder
python -m venv venv
source venv/bin/activate
pip install -e ".[dev]"
```

#### Development Workflow

1. Create a feature branch
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. Make changes following our code style (see below)

3. Write tests for your changes
   ```bash
   pytest tests/
   ```

4. Format code
   ```bash
   black src/ examples/
   flake8 src/
   ```

5. Commit with clear messages
   ```bash
   git add .
   git commit -m "Add feature: description of changes"
   ```

6. Push and create Pull Request
   ```bash
   git push origin feature/your-feature-name
   ```

### 4. Improve Documentation

Documentation improvements are always welcome!

- Fix typos
- Clarify examples
- Add guides
- Improve docstrings

## Code Style

### Python Style Guide

We follow [PEP 8](https://pep8.org/) with these tools:

- **black**: Code formatting
- **flake8**: Linting
- **pylint**: Code quality

### Format Code

```bash
# Auto-format
black src/ examples/

# Check style
flake8 src/
```

### Docstring Style

Use Google-style docstrings:

```python
def search_pubmed(query, mindate='2024/01/01', maxdate='2030/01/01'):
    """
    Search PubMed with automatic date-range splitting.
    
    Args:
        query (str): PubMed search query
        mindate (str): Start date in YYYY/MM/DD format
        maxdate (str): End date in YYYY/MM/DD format
    
    Returns:
        list: List of PMID strings
    
    Example:
        >>> pmids = search_pubmed('"test"[tiab]')
        >>> len(pmids)
        42
    """
```

## Testing

### Run Tests

```bash
pytest tests/
pytest tests/test_extraction.py -v  # Single file
pytest -k "test_search" -v  # By name
```

### Write Tests

```python
# tests/test_myfeature.py
import pytest
from pubmed_supervisor import my_feature

def test_my_feature():
    """Test description."""
    result = my_feature("input")
    assert result == "expected"

def test_my_feature_error():
    """Test error handling."""
    with pytest.raises(ValueError):
        my_feature(invalid_input)
```

## Commit Messages

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
type(scope): subject

body

footer
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation
- `style`: Formatting
- `refactor`: Code reorganization
- `test`: Tests
- `chore`: Build, dependencies

**Examples:**
```
feat(search): add query validation
fix(extraction): handle missing MeSH headings
docs(api): clarify return types
test(enrichment): add country detection tests
```

## Pull Request Guidelines

### Before Submitting

- [ ] Tests pass: `pytest`
- [ ] Code formatted: `black`
- [ ] Lints pass: `flake8`
- [ ] Documentation updated
- [ ] Docstrings added
- [ ] Related issues linked

### PR Template

```markdown
## Description
Brief description of changes.

## Related Issues
Fixes #123

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Documentation update
- [ ] Breaking change

## Testing
Describe testing performed.

## Checklist
- [ ] Tests pass
- [ ] Code formatted
- [ ] Documentation updated
- [ ] No new warnings
```

## Code Review Process

1. At least one maintainer review required
2. All CI checks must pass
3. Requested changes must be addressed
4. Approval → merge to main

## Development Tips

### Local Testing with Sample Data

```python
from pubmed_supervisor import search_pubmed

# Test with small dataset
pmids = search_pubmed('"test"[tiab]', mindate='2024/01/01', maxdate='2024/01/02')
# ... continue with limited data
```

### Debug Mode

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Now logs will show detailed information
pmids = search_pubmed(query)
```

### Profiling

```python
import cProfile
import pstats

profiler = cProfile.Profile()
profiler.enable()

# Your code here
papers = fetch_details(pmids)

profiler.disable()
stats = pstats.Stats(profiler)
stats.sort_stats('cumulative')
stats.print_stats(10)
```

## Project Structure

```
supervisor-finder/
├── src/pubmed_supervisor/  # Main package
│   ├── __init__.py
│   ├── config.py           # Configuration
│   ├── pubmed_search.py    # Search and fetch
│   ├── extraction.py       # Article extraction
│   ├── enrichment.py       # Data enrichment
│   ├── doi_lookup.py       # DOI handling
│   └── utils.py            # Utilities
├── tests/                  # Tests
├── examples/               # Example scripts
├── docs/                   # Documentation
├── data/sample/            # Sample data
└── README.md
```

## Release Process

1. Update version in `setup.py` and `src/pubmed_supervisor/__init__.py`
2. Update `CHANGELOG.md`
3. Create git tag: `git tag v0.2.0`
4. Push tag: `git push origin v0.2.0`
5. Build: `python setup.py sdist bdist_wheel`
6. Upload: `twine upload dist/*`

## Questions?

- 📖 Check [Documentation](docs/)
- 🐛 Search [Issues](https://github.com/yourusername/supervisor-finder/issues)
- 💬 Ask in [Discussions](https://github.com/yourusername/supervisor-finder/discussions)
- 📧 Email: your.email@example.com

## Recognition

Contributors are recognized in:
- CONTRIBUTORS.md file
- GitHub Contributors page
- Release notes for significant contributions

Thank you for contributing! 🎉
