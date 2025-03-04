import asyncio
import os
from pathlib import Path
from typing import List, Set
from urllib.parse import urljoin
import aiohttp
import aiofiles
import click
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
from pypdf import PdfWriter
from rich.console import Console
from rich.progress import Progress, TaskID
from rich.traceback import install
from tenacity import retry, stop_after_attempt, wait_exponential
from concurrent.futures import ThreadPoolExecutor

# Enable Rich traceback for better error handling
install()
console = Console()


class PDFDownloader:
    def __init__(self, download_dir: Path, concurrent_downloads: int = 5):
        self.download_dir = Path(download_dir)
        self.download_dir.mkdir(parents=True, exist_ok=True)
        self.semaphore = asyncio.Semaphore(concurrent_downloads)
        self.ua = UserAgent()
        self.progress: Progress = None
        self.task_id: TaskID = None
        self.downloaded_files: Set[Path] = set()

    @retry(
        stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    async def download_file(self, session: aiohttp.ClientSession, url: str) -> Path:
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
        headers = {"User-Agent": self.ua.random}
        async with aiohttp.ClientSession(headers=headers) as session:
            tasks = [self.download_file(session, url) for url in urls]
            return await asyncio.gather(*tasks, return_exceptions=True)


async def extract_pdf_links(html_file: str, headers: dict) -> List[str]:
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
    merger = PdfWriter()
    merger.metadata = None
    with ThreadPoolExecutor() as executor:
        list(executor.map(merger.append, pdf_files))

    with open(output, "wb") as output_file:
        merger.write(output_file)
    merger.close()


@click.command()
@click.argument("html_file")
@click.option("--output", "-o", default="combined_document.pdf")
@click.option("--download-dir", "-d", default="downloaded_pdfs")
@click.option("--concurrent-downloads", "-c", default=5)
def cli(
    html_file: str, output: str, download_dir: str, concurrent_downloads: int
) -> None:
    """Downloads and merges PDFs from Federal Register."""
    asyncio.run(main(html_file, output, download_dir, concurrent_downloads))


async def main(
    html_file: str, output: str, download_dir: str, concurrent_downloads: int
) -> None:
    console.rule("[bold blue]Federal Register PDF Downloader & Merger")

    ua = UserAgent()
    headers = {"User-Agent": ua.random}

    pdf_links = await extract_pdf_links(html_file, headers)
    if not pdf_links:
        console.print("[yellow]No PDFs found[/yellow]")
        return

    console.print(f"[green]Found {len(pdf_links)} PDFs[/green]")

    downloader = PDFDownloader(download_dir, concurrent_downloads)
    with Progress() as progress:
        downloader.progress = progress
        downloader.task_id = progress.add_task(
            "[cyan]Downloading...", total=len(pdf_links)
        )
        await downloader.download_all(pdf_links)

    if downloader.downloaded_files:
        console.print(f"[bold]Merging PDFs into: {output}[/bold]")
        merge_pdfs(downloader.downloaded_files, Path(output))
        console.print(f"[green]✔ Merged PDF saved as: {output}[/green]")


if __name__ == "__main__":
    cli()
