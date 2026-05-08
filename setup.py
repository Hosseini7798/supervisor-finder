"""
Setup configuration for supervisor-finder package.
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="supervisor-finder",
    version="0.1.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="Find academic supervisors from published articles via PubMed",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/supervisor-finder",
    project_urls={
        "Bug Tracker": "https://github.com/yourusername/supervisor-finder/issues",
        "Documentation": "https://github.com/yourusername/supervisor-finder/tree/main/docs",
        "Source Code": "https://github.com/yourusername/supervisor-finder",
    },
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering :: Bio-Informatics",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.8",
    install_requires=[
        "pandas>=1.3.0",
        "biopython>=1.79",
        "requests>=2.26.0",
        "beautifulsoup4>=4.9.0",
        "tqdm>=4.62.0",
    ],
    extras_require={
        "dev": [
            "pytest>=6.0",
            "black>=21.0",
            "flake8>=3.9",
            "sphinx>=4.0",
        ],
    },
    include_package_data=True,
    keywords=[
        "pubmed",
        "bioinformatics",
        "academic-research",
        "supervisor-finder",
        "data-mining",
    ],
)
