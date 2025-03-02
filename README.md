
# Download All Executive Orders

This project automates the process of downloading and merging all executive orders from a specified URL into a single PDF document.

## Project Structure

- `.github/workflows/download_and_merge.yml`: GitHub Actions workflow to automate the download and merge process.
- `main.py`: Python script to download and merge PDFs.
- `requirements.txt`: Python dependencies for the project.

## Usage

1. Clone the repository:

    ```sh
    git clone https://github.com/yourusername/Download-All-Executive-Orders.git
    cd Download-All-Executive-Orders
    ```

2. Install the required dependencies:

    ```sh
    pip install -r requirements.txt
    ```

3. Run the script:

    ```sh
    python main.py "https://www.federalregister.gov/presidential-documents/executive-orders/donald-trump/2025" --output combined_document.pdf --download-dir downloaded_pdfs
    ```

## GitHub Actions

The GitHub Actions workflow is set to run daily at midnight to download and merge the latest executive orders.

## License

This project is licensed under the MIT License.
