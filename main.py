import os
from urllib.parse import urljoin

import click
import requests
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
from pypdf import PdfWriter
from rich.console import Console
from rich.progress import Progress
from rich.traceback import install

# Enable Rich traceback for better error handling
install()
console = Console()

def download_file(url, folder):
    ua = UserAgent()
    headers = {'User-Agent': ua.random}
    local_filename = os.path.join(folder, url.split('/')[-1])
    
    # Check if the file already exists and is not empty
    if os.path.exists(local_filename) and os.path.getsize(local_filename) > 0:
        console.print(f"[yellow]File already exists and is not empty: {local_filename}[/yellow]")
        return local_filename

    with requests.get(url, headers=headers, stream=True) as r:
        r.raise_for_status()
        with open(local_filename, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
    return local_filename

def download_executive_orders(html_file, download_folder):
    with open(html_file, 'r', encoding='utf-8') as file:
        soup = BeautifulSoup(file, 'html.parser')
    
    if not os.path.exists(download_folder):
        os.makedirs(download_folder)
    
    console.print("[bold yellow]Debug: Checking all links in the HTML file[/bold yellow]")
    for link in soup.find_all('a', href=True):
        console.print(f"Debug: Found link - {link['href']}")
        if 'pdf' in link['href']:
            pdf_url = link['href']
            if not pdf_url.startswith('http'):
                pdf_url = urljoin('https://www.federalregister.gov', pdf_url)
            console.print(f"Downloading {pdf_url}")
            download_file(pdf_url, download_folder)

@click.command()
@click.argument("html_file")
@click.option(
    "--output", "-o", default="combined_document.pdf",
    help="Filename for the merged PDF output."
)
@click.option(
    "--download-dir", "-d", default="downloaded_pdfs",
    help="Directory to save downloaded PDFs."
)
def download_and_merge_pdfs(html_file, output, download_dir):
    """
    Downloads all official PDFs from a Federal Register HTML file and merges them into a single PDF.
    """
    ua = UserAgent()
    headers = {'User-Agent': ua.random}

    console.rule("[bold blue]Federal Register PDF Downloader & Merger")
    console.print(f"Processing file: {html_file}", style="bold green")

    os.makedirs(download_dir, exist_ok=True)

    if html_file.startswith("http"):
        response = requests.get(html_file, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
    else:
        with open(html_file, 'r', encoding='utf-8') as file:
            soup = BeautifulSoup(file, 'html.parser')

    # console.print("[bold yellow]Debug: Checking all links in the HTML file[/bold yellow]")
    # # Print all links, their attributes, text, and parent elements for debugging
    # for link in soup.find_all("a", href=True):
    #     console.print(f"Debug: Link - {link['href']}, Attributes - {link.attrs}, Text - {link.text}, Parent - {link.parent}")

    # Extract potential PDF links
    pdf_links = [
        link["href"] for link in soup.find_all("a", href=True)
        if link["href"].endswith(".pdf") and "govinfo.gov" in link["href"]
    ]

    if not pdf_links:
        console.print("[yellow]No official PDFs found in the file.[/yellow]")
        return

    console.print(f"[green]Found {len(pdf_links)} PDFs:[/green]")
    for link in pdf_links[:5]:  # Show only first 5 links for brevity
        console.print(f"- {link}")

    merger = PdfWriter()

    with Progress() as progress:
        task = progress.add_task("[cyan]Downloading PDFs...", total=len(pdf_links))

        for pdf_url in pdf_links:
            # Ensure full URL (some may be relative)
            if not pdf_url.startswith("http"):
                pdf_url = urljoin("https://www.govinfo.gov", pdf_url)

            pdf_filename = os.path.join(download_dir, os.path.basename(pdf_url))

            console.print(f"Downloading: {pdf_url}", style="blue")
            pdf_response = requests.get(pdf_url, headers=headers)

            if pdf_response.status_code == 200:
                with open(pdf_filename, "wb") as pdf_file:
                    pdf_file.write(pdf_response.content)
                console.print(f"✔ Saved: {pdf_filename}", style="green")
                merger.append(pdf_filename)
            else:
                console.print(f"[red]Failed to download {pdf_url}[/red]")

            progress.update(task, advance=1)

    # Save merged PDF
    console.print(f"[bold]Merging PDFs into: {output}[/bold]", style="cyan")
    with open(output, "wb") as output_pdf:
        merger.write(output_pdf)
    merger.close()
    console.print(f"[green]✔ Merged PDF saved as: {output}[/green]")

if __name__ == "__main__":
    download_and_merge_pdfs()
    html_file = 'example.html'
    download_folder = 'executive_orders'
    download_executive_orders(html_file, download_folder)
