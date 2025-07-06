"""Tests for PDF processing functions."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from pypdf import PdfReader, PdfWriter

from executive_orders_pdf import extract_pdf_links, merge_pdfs
from executive_orders_pdf.utils import PDFUtils


# Skip the complex async mocking test for now
@pytest.mark.skip("Complex async mocking - skipping for now")
@pytest.mark.asyncio
async def test_extract_pdf_links_from_url():
    """Test extracting PDF links from a URL."""
    pass


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

    # Create the patches
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
    # Create mock PDF files with proper naming format (YYYY-NNNNN.pdf)
    pdf_files = {Path("2025-01850.pdf"), Path("2025-01851.pdf"), Path("2025-01852.pdf")}

    # Create mock writers returned by clean_pdf_for_deterministic_output
    mock_writers = []
    for _ in range(3):
        mock_writer = MagicMock()
        mock_page = MagicMock()
        mock_writer.pages = [mock_page]
        mock_writers.append(mock_writer)

    # Create mock merged PDF writer
    mock_merger = MagicMock(spec=PdfWriter)

    # Mock PdfReader to return fake content
    mock_reader = MagicMock()
    mock_reader.pages = [MagicMock()]

    # Mock the date extraction to return a valid date after Jan 20, 2025
    mock_date_text = "Dated: January 21, 2025"
    mock_reader.pages[0].extract_text.return_value = mock_date_text

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
