"""Core functionality for downloading and merging PDFs from the Federal Register."""

import asyncio
from pathlib import Path
from typing import List, Set

import aiofiles
import aiohttp
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
from pypdf import PdfReader, PdfWriter
from rich.console import Console
from rich.progress import Progress, TaskID
from rich.traceback import install
from tenacity import retry, stop_after_attempt, wait_exponential

# Enable Rich traceback for better error handling
install()
console = Console()


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
        self.download_dir.mkdir(parents=True, exist_ok=True)
        self.concurrent_downloads = concurrent_downloads
        self.semaphore = asyncio.Semaphore(concurrent_downloads)
        self.ua = UserAgent()
        self.progress: Progress = None
        self.task_id: TaskID = None
        self.downloaded_files: Set[Path] = set()

    @retry(
        stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    async def download_file(self, session: aiohttp.ClientSession, url: str) -> Path:
        """
        Download a single PDF file with retry capability.

        Args:
            session: aiohttp client session
            url: URL of the PDF to download

        Returns:
            Path to the downloaded file
        """
        local_filename = self.download_dir / Path(url).name

        if local_filename.exists() and local_filename.stat().st_size > 0:
            console.print(f"[yellow]File exists: {local_filename}[/yellow]")
            self.downloaded_files.add(local_filename)
            return local_filename

        async with self.semaphore:
            async with session.get(url) as response:
                response.raise_for_status()
                async with aiofiles.open(local_filename, "wb") as f:
                    await f.write(await response.read())

                self.downloaded_files.add(local_filename)
                if self.progress:
                    self.progress.update(self.task_id, advance=1)

                return local_filename

    async def download_all(self, urls: List[str]) -> List[Path]:
        """
        Download multiple PDFs concurrently.

        Args:
            urls: List of PDF URLs to download

        Returns:
            List of paths to the downloaded files
        """
        headers = {"User-Agent": self.ua.random}
        async with aiohttp.ClientSession(headers=headers) as session:
            tasks = [self.download_file(session, url) for url in urls]
            return await asyncio.gather(*tasks, return_exceptions=True)


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


def clean_pdf_for_deterministic_output(pdf_path: Path) -> PdfWriter:
    """
    Clean a PDF to make it more deterministic by removing all potential sources of
    non-deterministic content like timestamps and random identifiers.

    Args:
        pdf_path: Path to the PDF file

    Returns:
        PdfWriter with cleaned PDF content
    """
    reader = PdfReader(pdf_path)
    writer = PdfWriter()

    # Copy pages without any metadata
    for page in reader.pages:
        writer.add_page(page)

    # First compress identical objects, then remove metadata
    # This avoids the error with None._info.indirect_reference
    writer.compress_identical_objects(remove_identicals=True, remove_orphans=True)
    writer.metadata = None

    return writer


def merge_pdfs(pdf_files: Set[Path], output: Path) -> None:
    """
    Merge multiple PDFs into a single file with deterministic output.

    Args:
        pdf_files: Set of PDF file paths to merge
        output: Output path for the merged PDF
    """
    # Sort the PDF files by path to ensure consistent order
    sorted_pdf_files = sorted(pdf_files)

    merger = PdfWriter()

    # First clean each PDF to make it deterministic
    for pdf_path in sorted_pdf_files:
        cleaned_writer = clean_pdf_for_deterministic_output(pdf_path)

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
            "[red]Error: cli.py not found. Please make sure it exists in the same directory.[/red]"  # noqa: E501
        )
        sys.exit(1)
