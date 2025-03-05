#!/usr/bin/env python3
"""
Script to generate summary information for PDF files in the repository.
It scans for PDFs, extracts metadata, and saves the information as JSON.
"""

import argparse
import glob
import json
import os
from datetime import datetime

from pypdf import PdfReader


def get_pdf_info(pdf_path):
    """
    Extract metadata from a PDF file.

    Args:
        pdf_path: Path to the PDF file

    Returns:
        Dictionary with PDF metadata or None if processing failed
    """
    try:
        reader = PdfReader(pdf_path)
        num_pages = len(reader.pages)

        # Get file stats
        stats = os.stat(pdf_path)
        size_mb = stats.st_size / (1024 * 1024)
        last_modified = datetime.fromtimestamp(stats.st_mtime).strftime("%Y-%m-%d")

        # Parse filename to get president and year
        filename = os.path.basename(pdf_path)
        president = "Unknown"
        year = "Unknown"

        parts = filename.replace(".pdf", "").split("_")
        if len(parts) >= 3:
            president = parts[0].replace("-", " ").title()
            year = parts[-1]

        return {
            "filename": filename,
            "president": president,
            "year": year,
            "pages": num_pages,
            "size_mb": round(size_mb, 2),
            "last_modified": last_modified,
        }
    except Exception as e:
        print(f"Error processing {pdf_path}: {str(e)}")
        return None


def main(priority_president="trump"):
    """
    Main function to scan for PDFs and generate summary information.

    Args:
        priority_president: President name to prioritize in sorting (default: "trump")
    """
    # Find all PDFs in the repository
    pdf_files = glob.glob("*.pdf")
    pdf_summaries = []

    for pdf_file in pdf_files:
        info = get_pdf_info(pdf_file)
        if info:
            pdf_summaries.append(info)

    # Sort with priority president's executive orders first, then by year (descending)
    def sort_key(x):
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
    with open("pdf_summary.json", "w", encoding="utf-8") as f:
        json.dump(pdf_summaries, f, indent=2)

    print(f"Found {len(pdf_summaries)} PDF files")
    if pdf_summaries:
        print(f"Prioritizing {priority_president} in the listing")

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
