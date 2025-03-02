# Executive Orders PDF Downloader

Automatically downloads and combines Executive Orders from the Federal Register into a single PDF file.

## Latest Combined PDFs

📄 [Download Current Year's Executive Orders (PDF)](executive_orders_2025.pdf)

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
python main.py [URL] --output executive_orders_2025.pdf --download-dir downloaded_pdfs
```

## Development

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Run the script:

```bash
python main.py "https://www.federalregister.gov/presidential-documents/executive-orders/donald-trump/2025" --output executive_orders_2025.pdf --download-dir downloaded_pdfs
```

## GitHub Actions

The GitHub Actions workflow is set to run daily at midnight to download and merge the latest executive orders.

## License

This project is licensed under the MIT License.
