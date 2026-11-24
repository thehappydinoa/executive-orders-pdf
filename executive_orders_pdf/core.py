"""Core functionality for downloading and merging PDFs from the Federal Register."""

import asyncio
import hashlib
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter
from typing import Any
from urllib.parse import urlparse

import aiofiles
import aiohttp
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
from pypdf import PdfReader, PdfWriter
from tenacity import retry, stop_after_attempt, wait_exponential_jitter

from executive_orders_pdf.utils import (
    ConfigUtils,
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

        cpu_count = os.cpu_count() or 2
        auto_cap = max(1, cpu_count * 4)
        self.concurrent_downloads = max(1, min(concurrent_downloads, auto_cap))
        self.semaphore = asyncio.Semaphore(self.concurrent_downloads)
        self.ua = UserAgent()
        self.downloaded_files: set[Path] = set()
        self.failed_downloads: set[str] = set()
        self.http_timeout = aiohttp.ClientTimeout(
            total=120, sock_connect=20, sock_read=60
        )
        self.download_state_path = self.download_dir / ".download_state.json"
        self.download_state = self._load_download_state()
        console.print(
            f"[blue]Initialized PDFDownloader with {self.concurrent_downloads} concurrent downloads[/blue]"
        )

    def _load_download_state(self) -> dict[str, dict[str, Any]]:
        data = ConfigUtils.load_json_config(self.download_state_path)
        if isinstance(data, dict):
            return {
                key: value
                for key, value in data.items()
                if isinstance(key, str) and isinstance(value, dict)
            }
        return {}

    def _save_download_state(self) -> None:
        ConfigUtils.save_json_config(self.download_state, self.download_state_path)

    def _build_conditional_headers(self, url: str) -> dict[str, str]:
        state = self.download_state.get(url, {})
        headers: dict[str, str] = {}
        etag = state.get("etag")
        last_modified = state.get("last_modified")
        if isinstance(etag, str) and etag:
            headers["If-None-Match"] = etag
        if isinstance(last_modified, str) and last_modified:
            headers["If-Modified-Since"] = last_modified
        return headers

    def _record_download_state(
        self,
        url: str,
        local_filename: Path,
        response_headers: dict[str, str],
        status: str,
    ) -> None:
        file_hash = PDFUtils.compute_file_hash(local_filename)
        if file_hash is None:
            return
        self.download_state[url] = {
            "url": url,
            "filename": local_filename.name,
            "etag": response_headers.get("ETag"),
            "last_modified": response_headers.get("Last-Modified"),
            "local_hash": file_hash,
            "local_size": local_filename.stat().st_size,
            "status": status,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential_jitter(initial=1, max=10, jitter=1),
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
        local_filename = self.download_dir / Path(urlparse(url).path).name
        start_time = datetime.now()
        had_existing_file = local_filename.exists()
        wrote_new_file = False

        try:
            if local_filename.exists() and local_filename.stat().st_size > 0:
                state = self.download_state.get(url)
                if state and state.get("local_hash") == PDFUtils.compute_file_hash(
                    local_filename
                ):
                    console.print(
                        f"[green]Skipping unchanged file from manifest: {local_filename}[/green]"
                    )
                    self.downloaded_files.add(local_filename)
                    return local_filename
                if state is None and PDFUtils.verify_pdf(local_filename):
                    console.print(
                        f"[yellow]Using existing valid file without manifest entry: {local_filename}[/yellow]"
                    )
                    self.downloaded_files.add(local_filename)
                    return local_filename
                if not PDFUtils.quick_pdf_sanity_check(local_filename):
                    console.print(
                        f"[yellow]Existing file {local_filename} failed quick sanity check, re-downloading[/yellow]"
                    )
                    local_filename.unlink()

            async with self.semaphore:
                request_headers = self._build_conditional_headers(url)
                async with session.get(url, headers=request_headers) as response:
                    if (
                        response.status == 304
                        and local_filename.exists()
                        and local_filename.stat().st_size > 0
                    ):
                        console.print(
                            f"[green]Not modified (304), using cached file: {local_filename}[/green]"
                        )
                        self._record_download_state(
                            url, local_filename, dict(response.headers), "not_modified"
                        )
                        self.downloaded_files.add(local_filename)
                        return local_filename

                    response.raise_for_status()
                    content = await response.read()
                    if not PDFUtils.quick_pdf_sanity_check_bytes(content):
                        raise ValueError(
                            f"Downloaded content for {url} is not a valid PDF"
                        )

                    async with aiofiles.open(local_filename, "wb") as f:
                        await f.write(content)
                    wrote_new_file = True

                    if not PDFUtils.quick_pdf_sanity_check(local_filename):
                        raise ValueError(
                            f"Downloaded PDF {local_filename} failed quick sanity check"
                        )
                    if not PDFUtils.verify_pdf(local_filename):
                        raise ValueError(
                            f"Downloaded PDF {local_filename} failed verification"
                        )

                    self._record_download_state(
                        url, local_filename, dict(response.headers), "downloaded"
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
            if wrote_new_file and local_filename.exists() and not had_existing_file:
                local_filename.unlink()
            raise

    async def download_all(self, urls: list[str]) -> list[Path]:
        """
        Download multiple PDFs concurrently with enhanced error handling.

        Args:
            urls: List of PDF URLs to download

        Returns:
            List of paths to the downloaded files
        """
        console.print(f"[blue]Starting download of {len(urls)} PDFs[/blue]")
        headers = {"User-Agent": self.ua.random}

        start = perf_counter()
        with ProgressTracker(len(urls), "Downloading PDFs"):
            connector = aiohttp.TCPConnector(
                limit=self.concurrent_downloads,
                limit_per_host=self.concurrent_downloads,
                ttl_dns_cache=300,
            )
            async with aiohttp.ClientSession(
                headers=headers, timeout=self.http_timeout, connector=connector
            ) as session:
                tasks = [self.download_file(session, url) for url in urls]
                results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results and log failures
        successful_downloads: list[Path] = []
        for url, result in zip(urls, results, strict=False):
            if isinstance(result, Exception):
                console.print(f"[red]Failed to download {url}: {str(result)}[/red]")
                self.failed_downloads.add(url)
            elif isinstance(result, Path):
                successful_downloads.append(result)
            else:
                console.print(
                    f"[red]Failed to download {url}: unexpected result type {type(result).__name__}[/red]"
                )
                self.failed_downloads.add(url)

        console.print(
            f"[blue]Download complete. [green]Successful: {len(successful_downloads)}[/green], "
            f"[red]Failed: {len(self.failed_downloads)}[/red][/blue]"
        )
        if self.failed_downloads:
            console.print(
                "[yellow]Failed URLs: " + ", ".join(self.failed_downloads) + "[/yellow]"
            )

        self._save_download_state()
        download_duration = perf_counter() - start
        console.print(
            f"[dim]Download stage completed in {download_duration:.2f}s[/dim]"
        )

        return successful_downloads


async def extract_pdf_links(html_file: str, headers: dict) -> list[str]:
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
        with open(html_file, encoding="utf-8") as f:
            content = f.read()

    soup = BeautifulSoup(content, "html.parser")
    pdf_links: list[str] = []
    for link in soup.find_all("a", href=True):
        href = link.get("href")
        if not isinstance(href, str):
            continue

        parsed_href = urlparse(href)
        host = parsed_href.hostname or ""
        if not parsed_href.path.endswith(".pdf"):
            continue

        is_absolute_or_scheme_relative = parsed_href.scheme in {"http", "https"} or (
            not parsed_href.scheme and href.startswith("//")
        )
        if is_absolute_or_scheme_relative and (
            host == "govinfo.gov" or host.endswith(".govinfo.gov")
        ):
            pdf_links.append(href if parsed_href.scheme else f"https:{href}")
        elif not parsed_href.scheme and not host:
            normalized_path = "/" + parsed_href.path.lstrip("/")
            relative_url = f"https://www.govinfo.gov{normalized_path}"
            if parsed_href.query:
                relative_url += f"?{parsed_href.query}"
            if parsed_href.fragment:
                relative_url += f"#{parsed_href.fragment}"
            pdf_links.append(relative_url)

    return pdf_links


def merge_pdfs(pdf_files: set[Path], output: Path) -> bool:
    """
    Merge multiple PDFs into a single file with deterministic output.
    PDFs are sorted by Federal Register document number in descending order (newest first).
    Only includes executive orders from January 20th, 2025 onwards.

    Args:
        pdf_files: Set of PDF file paths to merge
        output: Output path for the merged PDF
    """
    FileSystemUtils.ensure_directory(output.parent)
    state_path = output.parent / ".merge_state.json"
    state_data = ConfigUtils.load_json_config(state_path)
    merge_state: dict[str, Any] = state_data if isinstance(state_data, dict) else {}
    metadata_cache: dict[str, Any] = (
        merge_state.get("pdf_metadata", {})
        if isinstance(merge_state.get("pdf_metadata"), dict)
        else {}
    )
    output_states: dict[str, Any] = (
        merge_state.get("outputs", {})
        if isinstance(merge_state.get("outputs"), dict)
        else {}
    )

    existing_pdf_files = sorted(path for path in pdf_files if path.exists())
    signature_payload: list[dict[str, Any]] = []
    for pdf_path in existing_pdf_files:
        stats = pdf_path.stat()
        signature_payload.append(
            {
                "path": str(pdf_path.resolve()),
                "size": stats.st_size,
                "mtime_ns": stats.st_mtime_ns,
            }
        )

    input_signature = hashlib.sha256(
        json.dumps(signature_payload, sort_keys=True).encode("utf-8")
    ).hexdigest()
    output_key = str(output.resolve())
    current_output_state = output_states.get(output_key, {})
    if (
        output.exists()
        and isinstance(current_output_state, dict)
        and current_output_state.get("input_signature") == input_signature
    ):
        console.print(
            f"[green]Merge skipped for {output}; inputs are unchanged[/green]"
        )
        return False

    merge_start = perf_counter()
    # Get document info for each PDF
    pdf_info: list[tuple[Path, int, datetime | None]] = []
    for pdf_path in pdf_files:
        try:
            if not PDFUtils.quick_pdf_sanity_check(pdf_path):
                console.print(
                    f"[yellow]Skipping {pdf_path.name}: failed quick PDF sanity check[/yellow]"
                )
                continue

            # Extract info from filename (format: YYYY-NNNNN.pdf)
            doc_num = int(pdf_path.stem.split("-")[1])
            cache_key = str(pdf_path.resolve())
            stats = pdf_path.stat()
            cached_metadata = metadata_cache.get(cache_key)
            if (
                isinstance(cached_metadata, dict)
                and cached_metadata.get("size") == stats.st_size
                and cached_metadata.get("mtime_ns") == stats.st_mtime_ns
            ):
                pub_date_value = cached_metadata.get("pub_date")
                pub_date = (
                    datetime.fromisoformat(pub_date_value)
                    if isinstance(pub_date_value, str) and pub_date_value
                    else None
                )
                doc_num = int(cached_metadata.get("doc_num", doc_num))
                pdf_info.append((pdf_path, doc_num, pub_date))
                continue

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
            metadata_cache[cache_key] = {
                "size": stats.st_size,
                "mtime_ns": stats.st_mtime_ns,
                "doc_num": doc_num,
                "pub_date": pub_date.isoformat() if pub_date else None,
            }
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
        return False

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
    output_states[output_key] = {
        "input_signature": input_signature,
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "merged_file_count": len(sorted_pdf_files),
    }
    merge_state["pdf_metadata"] = metadata_cache
    merge_state["outputs"] = output_states
    ConfigUtils.save_json_config(merge_state, state_path)
    merge_duration = perf_counter() - merge_start
    console.print(f"[dim]Merge stage completed in {merge_duration:.2f}s[/dim]")
    return True


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
        from executive_orders_pdf.cli import cli

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
