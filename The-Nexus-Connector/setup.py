"""Setup configuration for Nexus Unified AI Wrapper."""

from setuptools import setup, find_packages
from pathlib import Path

# Read the README file
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding="utf-8")

# Read requirements
requirements = (this_directory / "requirements.txt").read_text().splitlines()

setup(
    name="nexus-ai-wrapper",
    version="0.1.0",
    author="Nexus Team",
    author_email="support@nexus-ai.dev",
    description="A unified interface for multiple AI providers - Write once, run with any AI",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/nexus-unified-wrapper",
    project_urls={
        "Bug Tracker": "https://github.com/yourusername/nexus-unified-wrapper/issues",
        "Documentation": "https://nexus-ai.dev/docs",
        "Source Code": "https://github.com/yourusername/nexus-unified-wrapper",
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
        "Typing :: Typed",
    ],
    packages=find_packages(exclude=["tests", "tests.*", "examples", "docs"]),
    python_requires=">=3.8",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.0",
            "pytest-asyncio>=0.21",
            "pytest-cov>=4.0",
            "black>=23.0",
            "isort>=5.12",
            "mypy>=1.0",
            "pre-commit>=3.0",
            "ruff>=0.1",
        ],
        "docs": [
            "sphinx>=6.0",
            "sphinx-rtd-theme>=1.3",
            "sphinx-autodoc-typehints>=1.24",
        ],
    },
    entry_points={
        "console_scripts": [
            "nexus=nexus.cli:main",
        ],
    },
    include_package_data=True,
    package_data={
        "nexus": ["py.typed"],
    },
    zip_safe=False,
    keywords=[
        "ai",
        "artificial-intelligence", 
        "openai",
        "anthropic",
        "claude",
        "gemini",
        "grok",
        "deepseek",
        "unified-api",
        "wrapper",
        "llm",
        "large-language-model",
    ],
)