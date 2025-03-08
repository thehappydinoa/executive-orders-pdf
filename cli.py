"""Command-line interface for the executive-orders-pdf downloader."""

import asyncio
from pathlib import Path

import click
import yaml
from fake_useragent import UserAgent
from rich.console import Console
from rich.progress import Progress
from rich.traceback import install

from main import PDFDownloader, extract_pdf_links, merge_pdfs

# Enable Rich traceback for better error handling
install()
console = Console()


def load_config(config_file=None):
    """Load configuration from a YAML file."""
    default_config = {
        "download": {
            "concurrent_downloads": 5,
            "retry_attempts": 3,
        },
        "output": {
            "default_filename": "executive_orders.pdf",
            "download_dir": "downloaded_pdfs",
        },
        "url": {
            "base_url": "https://www.federalregister.gov/presidential-documents/executive-orders",  # noqa: E501
            "president": "donald-trump",
            "year": "2025",
        },
    }

    if config_file and Path(config_file).exists():
        try:
            with open(config_file, "r") as f:
                user_config = yaml.safe_load(f)
                if user_config:
                    # Deep merge user config with default config
                    for section, values in user_config.items():
                        if section in default_config:
                            default_config[section].update(values)
                        else:
                            default_config[section] = values
        except Exception as e:
            console.print(f"[yellow]Warning: Failed to load config file: {e}[/yellow]")

    return default_config


@click.command()
@click.argument("html_file", required=False)
@click.option("--output", "-o", help="Output file name")
@click.option("--download-dir", "-d", help="Directory to save downloaded PDFs")
@click.option(
    "--concurrent-downloads", "-c", type=int, help="Number of concurrent downloads"
)
@click.option("--config", "-f", help="Path to configuration file", default=None)
@click.option("--president", "-p", help="President name (e.g., donald-trump)")
@click.option("--year", "-y", help="Year to download executive orders for")
def cli(html_file, output, download_dir, concurrent_downloads, config, president, year):
    """Downloads and merges PDFs from Federal Register.

    First checks for missing PDFs and downloads them, then merges all PDFs.
    """
    # Load configuration
    app_config = load_config(config)

    # Set download directory if not provided
    if not download_dir:
        download_dir = app_config["output"]["download_dir"]
    download_path = Path(download_dir)
    download_path.mkdir(parents=True, exist_ok=True)

    # Set output filename if not provided
    if not output:
        output = app_config["output"]["default_filename"]
        # If using auto-generated URL, create a more descriptive filename
        if president and year:
            output = f"{president}_executive_orders_{year}.pdf"
    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Construct URL if not provided directly
    if not html_file:
        if not president:
            president = app_config["url"]["president"]
        if not year:
            year = app_config["url"]["year"]

        base_url = app_config["url"]["base_url"]
        html_file = f"{base_url}/{president}/{year}"

    # Set concurrent downloads if not provided
    if not concurrent_downloads:
        concurrent_downloads = app_config["download"]["concurrent_downloads"]

    # Run the download function if needed, then merge
    asyncio.run(
        download_and_merge(html_file, output_path, download_path, concurrent_downloads)
    )


async def download_and_merge(
    html_file: str, output: Path, download_dir: Path, concurrent_downloads: int
):
    """Download any missing PDFs and then merge all existing PDFs."""
    console.rule("[bold blue]Federal Register PDF Downloader & Merger")

    # Setup for extraction
    ua = UserAgent()
    headers = {"User-Agent": ua.random}

    # Extract PDF links
    pdf_links = await extract_pdf_links(html_file, headers)
    if not pdf_links:
        console.print("[yellow]No PDF links found to download[/yellow]")
        # Even if no links found, still try to merge existing PDFs
        existing_pdfs = set(download_dir.glob("*.pdf"))
        if existing_pdfs:
            console.print(f"[green]Found {len(existing_pdfs)} existing PDFs[/green]")
            console.print(f"[bold]Merging PDFs into: {output}[/bold]")
            merge_pdfs(existing_pdfs, output)
            console.print(f"[green]✔ Merged PDF saved as: {output}[/green]")
        else:
            console.print("[red]No PDFs found to merge[/red]")
        return

    console.print(f"[green]Found {len(pdf_links)} PDF links[/green]")

    # Setup downloader with progress bar
    downloader = PDFDownloader(download_dir, concurrent_downloads)
    with Progress() as progress:
        downloader.progress = progress
        downloader.task_id = progress.add_task(
            "[cyan]Downloading...", total=len(pdf_links)
        )
        await downloader.download_all(pdf_links)

    # Get all PDFs in the download directory, regardless of whether they were just downloaded
    all_pdfs = set(download_dir.glob("*.pdf"))
    if all_pdfs:
        console.print(f"[green]Found {len(all_pdfs)} PDFs in total[/green]")
        console.print(f"[bold]Merging PDFs into: {output}[/bold]")
        merge_pdfs(all_pdfs, output)
        console.print(f"[green]✔ Merged PDF saved as: {output}[/green]")
    else:
        console.print("[red]No PDFs found to merge[/red]")


if __name__ == "__main__":
    cli()
