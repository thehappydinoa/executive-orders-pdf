# Executive Orders PDF Downloader

Automatically downloads and combines Executive Orders from the Federal Register into a single PDF file.

## Latest Combined PDFs

📄 [Download Current Year's Executive Orders (PDF)](donald_trump_executive_orders_2025.pdf)

*These files are automatically updated daily through GitHub Actions.*

## Features

- Asynchronous PDF downloading
- Automatic daily updates
- Concurrent downloads with rate limiting
- Automatic retry on failure
- Progress tracking
- PDF merging

## Project Structure

- `.github/workflows/download_and_merge.yml`: GitHub Actions workflow to automate the download and merge process.
- `main.py`: Python script to download and merge PDFs.
- `requirements.txt`: Python dependencies for the project.

## Usage

```bash
python main.py [URL] --output donald_trump_executive_orders_2025.pdf --download-dir downloaded_pdfs
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
python main.py "https://www.federalregister.gov/presidential-documents/executive-orders/donald-trump/2025" --output executive_orders_2025.pdf --download-dir downloaded_pdfs
```

## Code Quality

This project uses the following tools to maintain code quality:

- **Black**: Code formatter that adheres to PEP 8 standards
- **isort**: Sorts and organizes imports
- **flake8**: Linter with flake8-bugbear for additional bug detection

These tools are automatically run as pre-commit hooks when you commit changes.

## GitHub Actions

The GitHub Actions workflow is set to run daily at midnight to download and merge the latest executive orders.

## License

This project is licensed under the MIT License.
