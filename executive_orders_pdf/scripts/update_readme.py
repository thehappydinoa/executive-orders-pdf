#!/usr/bin/env python3
"""
Script to update the README.md with PDF summary information.
It reads the generated JSON data and updates specific sections in the README.
"""

import argparse
import re
from datetime import datetime
from pathlib import Path

from executive_orders_pdf.utils import ConfigUtils, FileSystemUtils, console


def main(priority_president: str = "trump") -> None:
    """
    Main function to update the README.md with PDF summary information.

    Args:
        priority_president: President name to prioritize in the README (default: "trump")
    """
    # Ensure the combined_pdfs directory exists
    FileSystemUtils.ensure_directory(Path("combined_pdfs"))

    # Load the PDF summary
    pdf_summaries = ConfigUtils.load_json_config(Path("pdf_summary.json"))
    if not pdf_summaries:
        console.print("[red]Error: No PDF summaries found in pdf_summary.json[/red]")
        return

    # Read the existing README
    try:
        with open("README.md", encoding="utf-8") as f:
            readme_content = f.read()
    except FileNotFoundError:
        console.print("[red]Error: README.md not found[/red]")
        return

    # Create the PDF table for README
    pdf_table = ""  # Remove the header since it's already in the README
    pdf_table += "| President | Year | Pages | Size | Last Updated | Download |\n"
    pdf_table += "|:----------|:-----|:------|:-----|:-------------|:---------|\n"

    for pdf in pdf_summaries:
        pdf_table += f'| {pdf["president"]} | {pdf["year"]} | {pdf["pages"]} | {pdf["size_mb"]} MB | {pdf["last_modified"]} | '
        pdf_table += f'[Download](combined_pdfs/{pdf["filename"]}) |\n'

    # Get total statistics
    total_pages = sum(pdf.get("pages", 0) for pdf in pdf_summaries)
    total_size_mb = sum(pdf.get("size_mb", 0) for pdf in pdf_summaries)

    # Add summary statistics
    stats_text = "## Summary Statistics\n\n"
    stats_text += f"- **Total Executive Order Collections:** {len(pdf_summaries)}\n"
    stats_text += f"- **Total Pages:** {total_pages}\n"
    stats_text += f"- **Total Size:** {round(total_size_mb, 2)} MB\n"
    stats_text += f"- **Last Updated:** {datetime.now().strftime('%Y-%m-%d')}\n"

    # Define marker patterns to locate where to insert the dynamic content
    table_marker_start = "<!-- PDF_TABLE_START -->"
    table_marker_end = "<!-- PDF_TABLE_END -->"
    stats_marker_start = "<!-- STATS_START -->"
    stats_marker_end = "<!-- STATS_END -->"

    # Replace content between markers
    if table_marker_start in readme_content and table_marker_end in readme_content:
        readme_content = re.sub(
            f"{re.escape(table_marker_start)}.*?{re.escape(table_marker_end)}",
            f"{table_marker_start}\n{pdf_table}\n{table_marker_end}",
            readme_content,
            flags=re.DOTALL,
        )
    else:
        # If markers are missing, find the table section and replace it
        table_pattern = r"(## Available Executive Order Collections\n\n\|.*?\n\|.*?\n)((?:\|.*?\n)*)"
        if re.search(table_pattern, readme_content, re.DOTALL):
            readme_content = re.sub(
                table_pattern,
                f"{table_marker_start}\n{pdf_table}\n{table_marker_end}",
                readme_content,
                flags=re.DOTALL,
            )

    readme_content = re.sub(
        f"{re.escape(stats_marker_start)}.*?{re.escape(stats_marker_end)}",
        f"{stats_marker_start}\n{stats_text}\n{stats_marker_end}",
        readme_content,
        flags=re.DOTALL,
    )

    # Update the 'Latest Combined PDFs' section
    if pdf_summaries:
        # Get priority president's latest executive orders first
        priority_name = priority_president.lower()
        priority_pdfs = [
            pdf for pdf in pdf_summaries if priority_name in pdf["president"].lower()
        ]

        if priority_pdfs:
            latest_pdf = priority_pdfs[
                0
            ]  # Take the first priority PDF (should be latest year)
            president_display = latest_pdf["president"]
        else:
            latest_pdf = pdf_summaries[0]  # Fallback to first PDF if no priority PDFs
            president_display = latest_pdf["president"]

        latest_section = "## Latest Combined PDFs\n\n"
        latest_section += f"📄 [Download {president_display} Executive Orders {latest_pdf['year']} (PDF)](combined_pdfs/{latest_pdf['filename']})\n\n"
        latest_section += f"*Currently showing the latest executive orders from {president_display}.*\n\n"
        latest_section += "*These files are automatically updated daily through GitHub Actions and stored in the `combined_pdfs` folder.*"

        latest_pattern = r"(## Latest Combined PDFs.*?)(\n## |\Z)"
        if re.search(latest_pattern, readme_content, re.DOTALL):
            readme_content = re.sub(
                latest_pattern,
                latest_section + r"\n\n\2",
                readme_content,
                flags=re.DOTALL,
            )

    # Write the updated README
    with open("README.md", "w", encoding="utf-8") as f:
        f.write(readme_content)

    console.print("README.md has been updated with PDF summary information")
    if priority_pdfs:
        console.print(f"Featuring {president_display} as the prioritized president")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Update README with PDF summary information"
    )
    parser.add_argument(
        "--priority",
        default="trump",
        help="President name to prioritize in the README (default: trump)",
    )

    args = parser.parse_args()
    main(priority_president=args.priority)
