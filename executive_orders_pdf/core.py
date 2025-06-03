"""Core functionality for downloading and merging PDFs from the Federal Register."""

import asyncio
import re
from datetime import datetime
from pathlib import Path
from typing import List, Set

import aiofiles
import aiohttp
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
from pypdf import PdfReader, PdfWriter
from tenacity import retry, stop_after_attempt, wait_exponential

from executive_orders_pdf.utils import (
    FileSystemUtils,
    PDFUtils,
    ProgressTracker,
    console,
)


class PDFDownloader:
    """Downloads PDFs concurrently with rate limiting and progress tracking."""

    def __init__(self, download_dir: Path, concurrent_downloads: int = 5):
        """
        Initialize the PDF downloader.

        Args:
            download_dir: Directory to save downloaded PDFs
            concurrent_downloads: Maximum number of concurrent downloads
        """
        self.download_dir = Path(download_dir)
        FileSystemUtils.ensure_directory(self.download_dir)
        self.concurrent_downloads = concurrent_downloads
        self.semaphore = asyncio.Semaphore(concurrent_downloads)
        self.ua = UserAgent()
        self.downloaded_files: Set[Path] = set()
        self.failed_downloads: Set[str] = set()
        console.print(
            f"[blue]Initialized PDFDownloader with {concurrent_downloads} concurrent downloads[/blue]"
        )

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        reraise=True,
    )
    async def download_file(self, session: aiohttp.ClientSession, url: str) -> Path:
        """
        Download a single PDF file with retry capability and verification.

        Args:
            session: aiohttp client session
            url: URL of the PDF to download

        Returns:
            Path to the downloaded file

        Raises:
            Exception: If download fails after retries or PDF is invalid
        """
        local_filename = self.download_dir / Path(url).name
        start_time = datetime.now()

        try:
            if local_filename.exists() and local_filename.stat().st_size > 0:
                if PDFUtils.verify_pdf(local_filename):
                    console.print(
                        f"[yellow]Using existing valid file: {local_filename}[/yellow]"
                    )
                    self.downloaded_files.add(local_filename)
                    return local_filename
                else:
                    console.print(
                        f"[yellow]Existing file {local_filename} is invalid, re-downloading[/yellow]"
                    )
                    local_filename.unlink()

            async with self.semaphore:
                async with session.get(url) as response:
                    response.raise_for_status()
                    async with aiofiles.open(local_filename, "wb") as f:
                        content = await response.read()
                        await f.write(content)

                    if not PDFUtils.verify_pdf(local_filename):
                        raise ValueError(
                            f"Downloaded PDF {local_filename} failed verification"
                        )

                    download_time = (datetime.now() - start_time).total_seconds()
                    size_mb = local_filename.stat().st_size / (1024 * 1024)
                    console.print(
                        f"[green]Successfully downloaded {url} "
                        f"(Size: {size_mb:.2f}MB, Time: {download_time:.2f}s)[/green]"
                    )

                    self.downloaded_files.add(local_filename)
                    return local_filename

        except Exception as e:
            self.failed_downloads.add(url)
            console.print(f"[red]Error downloading {url}: {str(e)}[/red]")
            if local_filename.exists():
                local_filename.unlink()
            raise

    async def download_all(self, urls: List[str]) -> List[Path]:
        """
        Download multiple PDFs concurrently with enhanced error handling.

        Args:
            urls: List of PDF URLs to download

        Returns:
            List of paths to the downloaded files
        """
        console.print(f"[blue]Starting download of {len(urls)} PDFs[/blue]")
        headers = {"User-Agent": self.ua.random}

        with ProgressTracker(len(urls), "Downloading PDFs"):
            async with aiohttp.ClientSession(headers=headers) as session:
                tasks = [self.download_file(session, url) for url in urls]
                results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results and log failures
        successful_downloads = []
        for url, result in zip(urls, results):
            if isinstance(result, Exception):
                console.print(f"[red]Failed to download {url}: {str(result)}[/red]")
                self.failed_downloads.add(url)
            else:
                successful_downloads.append(result)

        console.print(
            f"[blue]Download complete. [green]Successful: {len(successful_downloads)}[/green], "
            f"[red]Failed: {len(self.failed_downloads)}[/red][/blue]"
        )
        if self.failed_downloads:
            console.print(
                "[yellow]Failed URLs: " + ", ".join(self.failed_downloads) + "[/yellow]"
            )

        return successful_downloads


async def extract_pdf_links(html_file: str, headers: dict) -> List[str]:
    """
    Extract PDF links from an HTML file or URL.

    Args:
        html_file: Path to local HTML file or URL
        headers: HTTP headers for requests

    Returns:
        List of PDF URLs
    """
    if html_file.startswith("http"):
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.get(html_file) as response:
                content = await response.text()
    else:
        with open(html_file, "r", encoding="utf-8") as f:
            content = f.read()

    soup = BeautifulSoup(content, "html.parser")
    return [
        link["href"]
        for link in soup.find_all("a", href=True)
        if link["href"].endswith(".pdf") and "govinfo.gov" in link["href"]
    ]


def merge_pdfs(pdf_files: Set[Path], output: Path) -> None:
    """
    Merge multiple PDFs into a single file with deterministic output.
    PDFs are sorted by Federal Register document number in descending order (newest first).
    Only includes executive orders from January 20th, 2025 onwards.

    Args:
        pdf_files: Set of PDF file paths to merge
        output: Output path for the merged PDF
    """
    # Get document info for each PDF
    pdf_info = []
    for pdf_path in pdf_files:
        try:
            # Extract info from filename (format: YYYY-NNNNN.pdf)
            doc_num = int(pdf_path.stem.split("-")[1])

            # Open PDF to get metadata
            reader = PdfReader(pdf_path)

            # Get the first page text to check document details
            first_page_text = reader.pages[0].extract_text()

            # Try to get the publication date from the PDF
            # Look for multiple date patterns
            try:
                # Define all possible date patterns
                date_patterns = [
                    # Look for "Dated:" field
                    r"Dated:\s*(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},\s+2025",
                    # Look for Federal Register publication date
                    r"(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},\s+2025",
                    # Look for specific Federal Register format
                    r"Filed\s+\d{1,2}(?:–|-)(?:January|February|March|April|May|June|July|August|September|October|November|December)(?:–|-)",
                ]

                pub_date = None
                all_dates = []

                # Find all dates in the document
                for pattern in date_patterns:
                    matches = re.finditer(pattern, first_page_text)
                    for match in matches:
                        date_str = match.group()
                        try:
                            if "Filed" in date_str:
                                # Extract month and day from "Filed" date format
                                parts = re.search(
                                    r"Filed\s+(\d{1,2})(?:–|-)(\w+)(?:–|-)", date_str
                                )
                                if parts:
                                    day = parts.group(1)
                                    month = parts.group(2)
                                    date_str = f"{month} {day}, 2025"
                            else:
                                # Clean up the date string
                                date_str = date_str.replace("Dated:", "").strip()

                            # Parse the date
                            date = datetime.strptime(date_str, "%B %d, %Y")
                            all_dates.append(date)
                        except (ValueError, AttributeError):
                            # Skip invalid date formats
                            console.print(
                                f"[dim]Skipping invalid date format: {date_str}[/dim]"
                            )
                            continue

                # If we found any dates, use the earliest one as the publication date
                if all_dates:
                    pub_date = min(all_dates)
                    console.print(
                        f"[blue]Found date {pub_date.strftime('%B %d, %Y')} for {pdf_path.name}[/blue]"
                    )
                else:
                    console.print(
                        f"[yellow]Warning: Could not find any dates in {pdf_path.name}, using doc number as proxy[/yellow]"
                    )

            except Exception as e:
                console.print(
                    f"[yellow]Warning: Error parsing date from {pdf_path.name}: {str(e)}[/yellow]"
                )
                pub_date = None

            # Skip if the document is from January 19th or earlier
            if pub_date and pub_date.date() <= datetime(2025, 1, 19).date():
                console.print(
                    f"[yellow]Skipping {pdf_path.name} (Doc #{doc_num}, Date: {pub_date.strftime('%B %d, %Y')})[/yellow]"
                )
                continue

            pdf_info.append((pdf_path, doc_num, pub_date))
        except Exception as e:
            console.print(
                f"[yellow]Warning: Could not parse info from {pdf_path.name}, skipping: {str(e)}[/yellow]"
            )
            continue

    # Sort by document number (descending) and filter by date
    INAUGURATION_DATE = datetime(2025, 1, 20)
    sorted_pdf_files = []

    # First sort by doc number (descending)
    pdf_info.sort(key=lambda x: x[1], reverse=True)

    # Then filter and create final list
    for pdf_path, doc_num, pub_date in pdf_info:
        if pub_date is not None:
            if pub_date.date() >= INAUGURATION_DATE.date():
                sorted_pdf_files.append((pdf_path, doc_num))
                console.print(
                    f"[blue]Including {pdf_path.name} (Doc #{doc_num}, Date: {pub_date.strftime('%B %d, %Y')})[/blue]"
                )
            else:
                console.print(
                    f"[yellow]Skipping {pdf_path.name} (Doc #{doc_num}, Date: {pub_date.strftime('%B %d, %Y')})[/yellow]"
                )
        else:
            # If we couldn't get the date, use doc number as a proxy
            # Doc numbers are assigned sequentially, so we can use them to estimate dates
            # Being more conservative with the cutoff
            if doc_num > 1800:  # Increased threshold to be safer
                sorted_pdf_files.append((pdf_path, doc_num))
                console.print(
                    f"[blue]Including {pdf_path.name} (Doc #{doc_num}, Date: Unknown)[/blue]"
                )
            else:
                console.print(
                    f"[yellow]Skipping {pdf_path.name} (Doc #{doc_num}, Date: Unknown - likely before Jan 20)[/yellow]"
                )

    if not sorted_pdf_files:
        console.print("[red]No valid PDFs found after filtering[/red]")
        return

    console.print("[blue]Merging PDFs in chronological order (newest first)[/blue]")
    merger = PdfWriter()

    # First clean each PDF to make it deterministic
    for pdf_path, doc_num in sorted_pdf_files:
        console.print(
            f"[yellow]Adding {pdf_path.name} (Doc #{doc_num}) to merged PDF[/yellow]"
        )
        cleaned_writer = PDFUtils.clean_pdf_for_deterministic_output(pdf_path)

        # Transfer all pages from the cleaned writer to the merger
        for page in cleaned_writer.pages:
            merger.add_page(page)

    # First compress identical objects, then remove metadata in the merged PDF as well
    merger.compress_identical_objects(remove_identicals=True, remove_orphans=True)
    merger.metadata = None

    # Write the merged PDF
    with open(output, "wb") as output_file:
        merger.write(output_file)
    merger.close()
    console.print(
        f"[green]Successfully merged {len(sorted_pdf_files)} PDFs into {output}[/green]"
    )


# For backwards compatibility, keep a simple command-line interface
if __name__ == "__main__":
    # Import here to avoid circular imports
    import sys

    # Print deprecation warning
    console.print(
        "[yellow]Warning: Using main.py directly is deprecated. "
        "Please use cli.py instead for enhanced functionality.[/yellow]"
    )

    # Forward to cli.py if it exists
    try:
        from cli import cli

        # If no arguments were provided, show help
        if len(sys.argv) == 1:
            console.print("[bold]Forwarding to cli.py with --help flag.[/bold]")
            sys.argv.append("--help")

        # Run the CLI
        cli()
    except ImportError:
        console.print(
            "[red]Error: cli.py not found. Please make sure it exists in the same directory.[/red]"
        )
        sys.exit(1)
