"""
Configuration settings for supervisor-finder.

This module handles configuration for PubMed API access and other settings.
"""

import os

# PubMed Entrez API Configuration
ENTREZ_EMAIL = os.getenv("ENTREZ_EMAIL", "your.email@example.com")
"""Your email address for PubMed Entrez API access (required).
Set via environment variable ENTREZ_EMAIL or update this value."""

# Request Configuration
REQUEST_TIMEOUT = 15
"""Timeout in seconds for HTTP requests."""

RATE_LIMIT_DELAY = 0.1
"""Delay in seconds between PubMed API requests (respects NCBI guidelines)."""

MAX_RETRIES = 3
"""Maximum number of retry attempts for failed API requests."""

# Threading Configuration
DEFAULT_WORKERS = 4
"""Default number of worker threads for parallel fetching."""

# Data Configuration
SCIMAGO_FILE = "scimagojr_2025.csv"
"""Path to SCImago journal rankings file (separator: ';', encoding: 'utf-8')."""
