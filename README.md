# Executive Orders PDF Downloader

A Python tool to download and merge executive order PDFs from the Federal Register. This tool helps you collect and organize executive orders from different presidents and years.

![GitHub Actions](https://github.com/thehappydinoa/executive-orders-pdf/actions/workflows/download_and_merge.yml/badge.svg)
![GitHub last commit](https://img.shields.io/github/last-commit/thehappydinoa/executive-orders-pdf)
![License](https://img.shields.io/github/license/thehappydinoa/executive-orders-pdf)
![Python Version](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12-blue)

## Features

- Download executive order PDFs from the Federal Register
- Merge multiple PDFs into a single file
- Generate summary information about PDF collections
- Update README with PDF statistics and download links
- Support for concurrent downloads with progress tracking
- Configurable through YAML configuration file

## Installation

### From PyPI (when available)

```bash
pip install executive-orders-pdf
```

### From Source

```bash
# Clone the repository
git clone https://github.com/yourusername/executive-orders-pdf.git
cd executive-orders-pdf

# Create and activate a virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install the package in development mode with development dependencies
pip install -e ".[dev]"
```

### Development Setup

For development, you can install the package with development dependencies:

```bash
# Install with development dependencies
pip install -e ".[dev]"

# Or install development dependencies separately
pip install pytest pytest-cov black isort flake8 pre-commit
```

## Usage

### Command Line Interface

The package provides three main commands:

1. **Download and Merge PDFs**

```bash
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
executive-orders-pdf --president donald-trump --year 2025

# Download Biden's 2025 executive orders
executive-orders-pdf --president joe-biden --year 2025
```

2. **Generate PDF Summary**

```bash
pdf-summary [OPTIONS]
```

Options:

- `--priority`: President name to prioritize in the listing (default: trump)

Example:

```bash
# Generate summary with Trump's orders first
pdf-summary --priority trump
```

3. **Update README**

```bash
update-readme [OPTIONS]
```

Options:

- `--priority`: President name to prioritize in the README (default: trump)

Example:

```bash
# Update README with Trump's orders first
update-readme --priority trump
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

```bash
# Clone the repository
git clone https://github.com/yourusername/executive-orders-pdf.git
cd executive-orders-pdf

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install development dependencies
pip install -r requirements-dev.txt

# Install the package in development mode
pip install -e .
```

### Running Tests

```bash
pytest
```

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for details.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Available Executive Order Collections

<!-- PDF_TABLE_START -->
| President | Year | Pages | Size | Last Updated | Download |
|:----------|:-----|:------|:-----|:-------------|:---------|
| Donald Trump | 2025 | 439 | 12.58 MB | 2025-04-19 05:04:57 | [Download](combined_pdfs/donald-trump_executive_orders_2025.pdf) |
| Joe Biden | 2025 | 63 | 0.83 MB | 2025-03-27 00:30:09 | [Download](combined_pdfs/joe-biden_executive_orders_2025.pdf) |

<!-- PDF_TABLE_END -->

<!-- STATS_START -->
## Summary Statistics

- **Total Executive Order Collections:** 2
- **Total Pages:** 502
- **Total Size:** 13.41 MB
- **Last Updated:** 2025-04-19

<!-- STATS_END -->

## Automated Workflow

This project includes a GitHub Actions workflow that automatically downloads and merges executive orders daily. You can run the same commands locally:

```bash
# Download and merge executive orders for a specific president and year
executive-orders-pdf \
  --president donald-trump \
  --year 2025 \
  --output combined_pdfs/donald-trump_executive_orders_2025.pdf

# Generate summary of all PDFs
pdf-summary --priority trump

# Update README with latest information
update-readme --priority trump
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
executive-orders-pdf --config config.yaml
```
