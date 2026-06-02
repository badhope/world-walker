"""
Regional Industrial Economic Analysis Platform - packaging configuration.

Installable via ``pip install .`` from the project root.
"""
from setuptools import setup, find_packages
from pathlib import Path

# Load long description from README
readme_file = Path(__file__).parent / "README.md"
long_description = ""
if readme_file.exists():
    with open(readme_file, "r", encoding="utf-8") as fh:
        long_description = fh.read()

# Load pinned runtime requirements
requirements_file = Path(__file__).parent / "requirements.txt"
requirements = []
if requirements_file.exists():
    with open(requirements_file, "r", encoding="utf-8") as f:
        requirements = [
            line.strip()
            for line in f
            if line.strip() and not line.startswith("#")
        ]

setup(
    name="regional-economic-analysis",
    version="4.0.0",
    author="Regional Economic Analysis Team",
    author_email="contact@example.com",
    description=(
        "Regional Industrial Economic Analysis Platform: a production-grade "
        "multi-scenario analytics system for city comparison, retail site "
        "selection, sales forecasting and government policy evaluation."
    ),
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/your-org/regional-economic-analysis",
    packages=find_packages(exclude=["tests", "tests.*", "examples", "docs", "notebooks"]),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "Intended Audience :: Financial and Insurance Industry",
        "Intended Audience :: Government",
        "License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3 :: Only",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Scientific/Engineering :: Information Analysis",
        "Topic :: Office/Business :: Financial :: Investment",
        "Topic :: Sociology",
        "Operating System :: OS Independent",
        "Natural Language :: English",
        "Natural Language :: Chinese (Simplified)",
    ],
    python_requires=">=3.11",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=8.0.0",
            "pytest-cov>=5.0.0",
            "pytest-mock>=3.12.0",
            "pytest-asyncio>=0.23.0",
            "ruff>=0.3.0",
            "black>=24.0.0",
            "mypy>=1.8.0",
        ],
        "api": [
            "fastapi>=0.115.0",
            "uvicorn[standard]>=0.32.0",
            "pydantic>=2.5.0",
            "pydantic-settings>=2.0.0",
        ],
        "viz": [
            "plotly>=5.18.0",
            "matplotlib>=3.8.0",
            "seaborn>=0.13.0",
        ],
        "ml": [
            "scikit-learn>=1.3.0",
            "statsmodels>=0.14.0",
            "joblib>=1.3.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "rea-api=backend.api.main:run",
            "regional-stats-api=backend.api.main:run",
        ],
    },
    include_package_data=True,
    package_data={
        "config": ["regions/*.json", "industries/*.json"],
        "examples": ["**/*.json", "**/*.py"],
    },
    zip_safe=False,
    keywords=[
        "regional-economy",
        "economic-analysis",
        "city-comparison",
        "industry-analysis",
        "retail-location",
        "sales-forecast",
        "site-selection",
        "policy-evaluation",
        "time-series-forecasting",
        "data-visualization",
        "fastapi",
        "echarts",
        "data-science",
        "machine-learning",
    ],
    project_urls={
        "Bug Reports": "https://github.com/your-org/regional-economic-analysis/issues",
        "Source": "https://github.com/your-org/regional-economic-analysis",
        "Documentation": "https://github.com/your-org/regional-economic-analysis/blob/main/README.md",
        "Changelog": "https://github.com/your-org/regional-economic-analysis/blob/main/CHANGELOG.md",
        "Examples": "https://github.com/your-org/regional-economic-analysis/tree/main/examples",
    },
)
