#!/usr/bin/env python3
"""
Script to generate summary information for PDF files in the repository.
It scans for PDFs, extracts metadata, and saves the information as JSON.
"""

import argparse
import glob
from pathlib import Path
from typing import Any

from executive_orders_pdf.utils import ConfigUtils, FileSystemUtils, PDFUtils, console


def main(priority_president: str = "trump") -> list[dict[str, Any]]:
    """
    Main function to scan for PDFs and generate summary information.

    Args:
        priority_president: President name to prioritize in sorting (default: "trump")
    """
    # Ensure the combined_pdfs directory exists
    combined_pdfs_dir = Path("combined_pdfs")
    FileSystemUtils.ensure_directory(combined_pdfs_dir)

    # Find all PDFs in the combined_pdfs directory
    pdf_files = [Path(f) for f in glob.glob("combined_pdfs/*.pdf")]

    # If no PDFs found in combined_pdfs, check for PDFs in root and move them
    if not pdf_files:
        root_pdfs = [Path(f) for f in glob.glob("*.pdf")]
        pdf_files = FileSystemUtils.move_files_to_directory(
            root_pdfs, combined_pdfs_dir
        )

    pdf_summaries = []

    for pdf_file in pdf_files:
        info = PDFUtils.get_pdf_info(pdf_file)
        if info:
            pdf_summaries.append(info)

    # Sort with priority president's executive orders first, then by year (descending)
    def sort_key(x: dict[str, Any]) -> tuple[int, int, str]:
        # Normalize names for comparison
        president_name = x["president"].lower()
        priority_name = priority_president.lower()

        # Check if this president matches the priority president
        is_priority = priority_name in president_name
        return (0 if is_priority else 1, x["year"], x["president"])

    pdf_summaries.sort(
        key=sort_key, reverse=False
    )  # False because we're using 0/1 for priority

    # Save the summary as JSON
    ConfigUtils.save_json_config(pdf_summaries, Path("pdf_summary.json"))

    console.print(f"Found {len(pdf_summaries)} PDF files")
    if pdf_summaries:
        console.print(f"Prioritizing {priority_president} in the listing")

    return pdf_summaries


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate PDF summary information")
    parser.add_argument(
        "--priority",
        default="trump",
        help="President name to prioritize in the listing (default: trump)",
    )

    args = parser.parse_args()
    main(priority_president=args.priority)
