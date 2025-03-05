# Executive Orders PDF Downloader

![GitHub Actions](https://github.com/thehappydinoa/executive-orders-pdf/actions/workflows/download_and_merge.yml/badge.svg)
![GitHub last commit](https://img.shields.io/github/last-commit/thehappydinoa/executive-orders-pdf)

Automatically downloads and combines Executive Orders from the Federal Register into a single PDF file.

## Latest Combined PDFs

📄 [Download Current Year's Executive Orders (PDF)](donald-trump_executive_orders_2025.pdf)

*These files are automatically updated daily through GitHub Actions.*

## Features

- Asynchronous PDF downloading
- Automatic daily updates
- Concurrent downloads with rate limiting
- Automatic retry on failure
- Progress tracking
- PDF merging
- Configuration file support
- Modular design with separate CLI module
- Comprehensive test suite

## Project Structure

- `.github/workflows/download_and_merge.yml`: GitHub Actions workflow to automate the download and merge process.
- `main.py`: Core functionality for downloading and merging PDFs.
- `cli.py`: Command-line interface implementation.
- `config.yaml`: Configuration file for customizing behavior.
- `requirements.txt`: Python dependencies for the project.
- `requirements-dev.txt`: Development dependencies.
- `tests/`: Test suite using pytest.

## Usage

### Basic Usage

```bash
python cli.py [URL] --output [OUTPUT_FILE] --download-dir [DOWNLOAD_DIR]
```

### Using Configuration File

You can also use a configuration file to set default options:

```bash
python cli.py --config config.yaml
```

### Specifying President and Year

```bash
python cli.py --president donald-trump --year 2025
```

## Development

1. Create and activate a virtual environment:

```bash
# On Windows
python -m venv venv
.\venv\Scripts\activate

# On macOS/Linux
python -m venv venv
source venv/bin/activate
```

2. Install dependencies

```bash
pip install -r requirements.txt
```

3. For development, install development dependencies

```bash
pip install -r requirements-dev.txt
```

4. Set up pre-commit hooks (Optional)

```bash
pre-commit install
```

5. Run the script

```bash
# Replace YYYY with the current year (e.g., 2025)
python cli.py --president donald-trump --year YYYY
```

For example, in 2025 you would run:

```bash
python cli.py --president donald-trump --year 2025
```

You can also use the configuration file:

```bash
python cli.py --config config.yaml
```

## Running Tests

Run the test suite with pytest:

```bash
pytest
```

## Code Quality

This project uses the following tools to maintain code quality:

- **Black**: Code formatter that adheres to PEP 8 standards
- **isort**: Sorts and organizes imports
- **flake8**: Linter with flake8-bugbear for additional bug detection

These tools are automatically run as pre-commit hooks when you commit changes.

## GitHub Actions

The GitHub Actions workflow is set to run daily at midnight to download and merge the latest executive orders.

## Contributing

Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on how to contribute to this project.

## License

This project is licensed under the MIT License.
