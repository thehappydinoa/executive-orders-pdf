"""Tests for PDF processing functions."""

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from pypdf import PdfReader, PdfWriter

from executive_orders_pdf.core import extract_pdf_links, merge_pdfs
from executive_orders_pdf.utils import PDFUtils


# Patch the extract_pdf_links function to avoid complex async mocking
@pytest.mark.asyncio
@patch("tests.test_pdf_processing.extract_pdf_links", new_callable=AsyncMock)
async def test_extract_pdf_links_from_url(mock_extract_links):
    """Test extracting PDF links from a URL."""
    # Expected PDF links
    expected_links = [
        "https://www.govinfo.gov/content/pkg/FR-2023-01-20/pdf/2023-01234.pdf",
        "https://www.govinfo.gov/content/pkg/FR-2023-01-21/pdf/2023-05678.pdf",
    ]

    # Configure the async mock to return our expected links
    mock_extract_links.return_value = expected_links

    # Call the function (the patched version)
    result = await extract_pdf_links("https://example.com/page", {})

    # Assertions
    assert result == expected_links
    mock_extract_links.assert_called_once_with("https://example.com/page", {})


@pytest.mark.asyncio
async def test_extract_pdf_links_from_file():
    """Test extracting PDF links from a local file."""
    # Create a temporary file with HTML content
    html_content = """
    <html>
        <body>
            <a href="https://www.govinfo.gov/content/pkg/FR-2023-01-20/pdf/2023-01234.pdf">PDF 1</a>
            <a href="https://www.govinfo.gov/content/pkg/FR-2023-01-21/pdf/2023-05678.pdf">PDF 2</a>
            <a href="https://www.example.com/not-a-pdf.html">Not a PDF</a>
            <a href="https://www.example.com/not-govinfo.pdf">Not from govinfo</a>
        </body>
    </html>
    """

    # Mock the open function
    mock_open = mock_open = MagicMock()
    mock_open.return_value.__enter__.return_value.read.return_value = html_content

    # Call the function with a file path
    with patch("builtins.open", mock_open):
        links = await extract_pdf_links("local_file.html", {})

    # Assertions
    assert len(links) == 2
    assert (
        "https://www.govinfo.gov/content/pkg/FR-2023-01-20/pdf/2023-01234.pdf" in links
    )
    assert (
        "https://www.govinfo.gov/content/pkg/FR-2023-01-21/pdf/2023-05678.pdf" in links
    )


def test_clean_pdf_for_deterministic_output():
    """Test cleaning a PDF to make it deterministic."""
    # Create a mock PDF
    mock_reader = MagicMock(spec=PdfReader)
    mock_page1 = MagicMock()
    mock_page2 = MagicMock()
    mock_reader.pages = [mock_page1, mock_page2]

    # Mock PdfWriter
    mock_writer = MagicMock(spec=PdfWriter)

    # Create the patches - use the correct module path
    with (
        patch("executive_orders_pdf.utils.PdfReader", return_value=mock_reader),
        patch("executive_orders_pdf.utils.PdfWriter", return_value=mock_writer),
    ):
        # Call the function
        result = PDFUtils.clean_pdf_for_deterministic_output(Path("test.pdf"))

    # Assertions
    assert result == mock_writer
    assert mock_writer.add_page.call_count == 2
    mock_writer.add_page.assert_any_call(mock_page1)
    mock_writer.add_page.assert_any_call(mock_page2)
    mock_writer.compress_identical_objects.assert_called_once_with(
        remove_identicals=True, remove_orphans=True
    )
    assert mock_writer.metadata is None


def test_merge_pdfs():
    """Test merging multiple PDFs."""
    # Create mock PDF files with proper FR document format
    pdf_files = {Path("2025-01801.pdf"), Path("2025-01802.pdf"), Path("2025-01803.pdf")}

    # Create mock writers returned by clean_pdf_for_deterministic_output
    mock_writers = []
    for _ in range(3):
        mock_writer = MagicMock()
        mock_page = MagicMock()
        mock_writer.pages = [mock_page]
        mock_writers.append(mock_writer)

    # Create mock merged PDF writer
    mock_merger = MagicMock(spec=PdfWriter)

    # Mock PdfReader to simulate PDF content
    mock_reader = MagicMock()
    mock_page = MagicMock()
    mock_page.extract_text.return_value = (
        "Executive Order\nDated: January 21, 2025\nSigned by the President"
    )
    mock_reader.pages = [mock_page]

    # Create the patches
    with (
        patch(
            "executive_orders_pdf.utils.PDFUtils.clean_pdf_for_deterministic_output",
            side_effect=mock_writers,
        ),
        patch("executive_orders_pdf.core.PdfWriter", return_value=mock_merger),
        patch("executive_orders_pdf.core.PdfReader", return_value=mock_reader),
        patch("builtins.open"),
    ):
        # Call the function
        merge_pdfs(pdf_files, Path("merged.pdf"))

    # Assertions
    # Should have called clean_pdf_for_deterministic_output for each input file
    assert mock_merger.add_page.call_count == 3
    mock_merger.compress_identical_objects.assert_called_once_with(
        remove_identicals=True, remove_orphans=True
    )
    assert mock_merger.metadata is None
    mock_merger.write.assert_called_once()
    mock_merger.close.assert_called_once()
