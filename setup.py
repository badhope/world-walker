"""
区域产业经济分析平台 - 安装配置

支持通过pip install安装本项目
"""
from setuptools import setup, find_packages
from pathlib import Path

# 读取README
readme_file = Path(__file__).parent / "README.md"
long_description = ""
if readme_file.exists():
    with open(readme_file, "r", encoding="utf-8") as fh:
        long_description = fh.read()

# 读取requirements.txt
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
    name="national-stats-analyzer",
    version="4.0.0",
    author="区域产业经济分析团队",
    author_email="contact@example.com",
    description="区域产业经济分析平台 - 面向求职的可复用分析工具",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/your-project/national-stats-analyzer",
    packages=find_packages(exclude=["tests", "tests.*", "examples", "docs"]),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering :: Information Analysis",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.9",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "mypy>=1.0.0",
        ],
        "api": [
            "fastapi>=0.100.0",
            "uvicorn>=0.23.0",
            "starlette>=0.27.0",
        ],
        "visualization": [
            "plotly>=5.15.0",
            "pyecharts>=2.0.4",
        ],
    },
    entry_points={
        "console_scripts": [
            "national-stats=main:main",
            "national-stats-api=main:main",
        ],
    },
    include_package_data=True,
    package_data={
        "config": ["regions/*.json", "industries/*.json"],
        "examples": ["**/*.json", "**/*.py"],
    },
    zip_safe=False,
    keywords=[
        "economic-analysis",
        "regional-industry",
        "semiconductor",
        "data-analysis",
        "visualization",
        "fastapi",
        "plotly",
    ],
    project_urls={
        "Bug Reports": "https://github.com/your-project/national-stats-analyzer/issues",
        "Source": "https://github.com/your-project/national-stats-analyzer",
        "Documentation": "https://github.com/your-project/national-stats-analyzer/docs",
        "Examples": "https://github.com/your-project/national-stats-analyzer/examples",
    },
)
