# Executive Orders PDF Downloader

A Python tool to download and merge executive order PDFs from the Federal Register. This tool helps you collect and organize executive orders from different presidents and years.

[![GitHub Actions](https://github.com/thehappydinoa/executive-orders-pdf/actions/workflows/main.yml/badge.svg)](https://github.com/thehappydinoa/executive-orders-pdf/actions/workflows/main.yml)
[![GitHub last commit](https://img.shields.io/github/last-commit/thehappydinoa/executive-orders-pdf)](https://github.com/thehappydinoa/executive-orders-pdf/commits/main/)
[![License](https://img.shields.io/github/license/thehappydinoa/executive-orders-pdf)](https://github.com/thehappydinoa/executive-orders-pdf/blob/main/LICENSE)
[![Python Version](https://img.shields.io/badge/python-3.9%20%7C%203.10%20%7C%203.11%20%7C%203.12-blue)](https://github.com/thehappydinoa/executive-orders-pdf/blob/main/pyproject.toml)

## Features

- Download executive order PDFs from the Federal Register
- Merge multiple PDFs into a single file
- Generate summary information about PDF collections
- Update README with PDF statistics and download links
- Support for concurrent downloads with progress tracking
- Configurable through YAML configuration file

## Installation

### Using uv (Recommended)

[uv](https://github.com/astral-sh/uv) is a fast Python package manager. Install it first if you haven't:

```bash
# Install uv (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh  # Unix/macOS
# or
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"  # Windows

# Install the package
uv add executive-orders-pdf
```

### From Source with uv

```bash
# Clone the repository
git clone https://github.com/thehappydinoa/executive-orders-pdf.git
cd executive-orders-pdf

# Install dependencies and the package
uv sync
```

### Traditional pip Installation

```bash
# From PyPI (when available)
pip install executive-orders-pdf

# From source
git clone https://github.com/thehappydinoa/executive-orders-pdf.git
cd executive-orders-pdf

# Create and activate a virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install the package in development mode with development dependencies
pip install -e ".[dev]"
```

## Usage

### Command Line Interface

The package provides three main commands:

1. **Download and Merge PDFs**

```bash
# With uv
uv run executive-orders-pdf [OPTIONS] [HTML_FILE]

# With pip (if installed globally)
executive-orders-pdf [OPTIONS] [HTML_FILE]
```

Options:

- `--output, -o`: Output file name
- `--download-dir, -d`: Directory to save downloaded PDFs
- `--concurrent-downloads, -c`: Number of concurrent downloads
- `--config, -f`: Path to configuration file
- `--president, -p`: President name (e.g., donald-trump)
- `--year, -y`: Year to download executive orders for

Example:

```bash
# Download Trump's 2025 executive orders
uv run executive-orders-pdf --president donald-trump --year 2025

# Download Biden's 2025 executive orders
uv run executive-orders-pdf --president joe-biden --year 2025
```

2. **Generate PDF Summary**

```bash
# With uv
uv run pdf-summary [OPTIONS]

# With pip
pdf-summary [OPTIONS]
```

Options:

- `--priority`: President name to prioritize in the listing (default: trump)

Example:

```bash
# Generate summary with Trump's orders first
uv run pdf-summary --priority trump
```

3. **Update README**

```bash
# With uv
uv run update-readme [OPTIONS]

# With pip
update-readme [OPTIONS]
```

Options:

- `--priority`: President name to prioritize in the README (default: trump)

Example:

```bash
# Update README with Trump's orders first
uv run update-readme --priority trump
```

### Python API

You can also use the package as a Python library:

```python
from executive_orders_pdf import PDFDownloader, merge_pdfs
from pathlib import Path

# Download PDFs
downloader = PDFDownloader(download_dir=Path("downloaded_pdfs"))
pdf_files = await downloader.download_all(pdf_urls)

# Merge PDFs
merge_pdfs(pdf_files, output=Path("merged.pdf"))
```

## Configuration

You can configure the tool using a YAML file. Create a `config.yaml` file:

```yaml
download:
  concurrent_downloads: 5
  retry_attempts: 3

output:
  default_filename: executive_orders.pdf
  download_dir: downloaded_pdfs

url:
  base_url: https://www.federalregister.gov/presidential-documents/executive-orders
  president: donald-trump
  year: 2025
```

Then use it with the `--config` option:

```bash
executive-orders-pdf --config config.yaml
```

## Project Structure

```
executive_orders_pdf/
├── __init__.py
├── core.py          # Core functionality
├── cli.py           # Command-line interface
├── utils.py         # Utility functions
└── scripts/         # Command-line utility scripts
    ├── __init__.py
    ├── pdf_summary.py
    └── update_readme.py
```

## Development

### Setup Development Environment

#### Using uv (Recommended)

```bash
# Clone the repository
git clone https://github.com/thehappydinoa/executive-orders-pdf.git
cd executive-orders-pdf

# Install all dependencies (including dev dependencies)
uv sync --dev

# Install pre-commit hooks
uv run pre-commit install
```

#### Using pip (Traditional)

```bash
# Clone the repository
git clone https://github.com/thehappydinoa/executive-orders-pdf.git
cd executive-orders-pdf

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install development dependencies
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install
```

### Running Tests

```bash
# With uv
uv run pytest

# With activated venv
pytest
```

### Code Quality

We use several tools to maintain code quality:

```bash
# Run all pre-commit hooks
uv run pre-commit run --all-files

# Or individual tools:
uv run black .                    # Format code
uv run isort .                    # Sort imports
uv run flake8                     # Lint code
uv run mypy executive_orders_pdf  # Type checking
uv run bandit -r executive_orders_pdf  # Security scan
```

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for details.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Available Executive Order Collections

<!-- PDF_TABLE_START -->
| President | Year | Pages | Size | Last Updated | Download |
|:----------|:-----|:------|:-----|:-------------|:---------|
| Donald Trump | 2025 | 1103 | 59.64 MB | 2025-12-19 05:07:19 | [Download](combined_pdfs/donald-trump_executive_orders_2025.pdf) |
| Joe Biden | 2025 | 63 | 0.83 MB | 2025-11-25 20:31:45 | [Download](combined_pdfs/joe-biden_executive_orders_2025.pdf) |

<!-- PDF_TABLE_END -->

<!-- STATS_START -->
## Summary Statistics

- **Total Executive Order Collections:** 2
- **Total Pages:** 1166
- **Total Size:** 60.47 MB
- **Last Updated:** 2025-12-19

<!-- STATS_END -->

## Automated Workflow

This project includes a GitHub Actions workflow that automatically downloads and merges executive orders daily. You can run the same commands locally:

```bash
# Download and merge executive orders for a specific president and year
uv run executive-orders-pdf \
  --president donald-trump \
  --year 2025 \
  --output combined_pdfs/donald-trump_executive_orders_2025.pdf

# Generate summary of all PDFs
uv run pdf-summary --priority trump

# Update README with latest information
uv run update-readme --priority trump
```

The workflow runs these commands in sequence:

1. Downloads and merges PDFs for the specified president and year
2. Generates a summary of all PDFs
3. Updates the README with the latest information

You can also use the configuration file to set default values:

```yaml
# config.yaml
url:
  president: donald-trump
  year: 2025
output:
  default_filename: combined_pdfs/donald-trump_executive_orders_2025.pdf
```

Then run:

```bash
uv run executive-orders-pdf --config config.yaml
```
