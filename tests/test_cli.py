"""Tests for the CLI module."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

# Import the cli functions - using a try/except to handle potential import issues
try:
    from executive_orders_pdf.cli import cli, load_config
except ImportError:
    # Skip these tests if cli.py doesn't exist
    pytestmark = pytest.mark.skip("cli.py module not found")


def test_load_config_default():
    """Test loading default configuration when no file is provided."""
    config = load_config(None)

    # Verify default values
    assert config["download"]["concurrent_downloads"] == 5
    assert config["output"]["download_dir"] == "downloaded_pdfs"
    assert config["url"]["president"] == "donald-trump"
    assert config["url"]["year"] == "2025"


def test_load_config_custom():
    """Test loading custom configuration from a file."""
    # Create a temporary config file
    config_data = {
        "download": {
            "concurrent_downloads": 10,
            "retry_attempts": 5,
        },
        "output": {
            "default_filename": "custom.pdf",
        },
        "url": {
            "president": "biden",
            "year": "2023",
        },
    }

    # Mock the file operations
    with (
        patch("builtins.open", MagicMock()),
        patch("yaml.safe_load", return_value=config_data),
    ):
        # Mock Path.exists to return True
        with patch.object(Path, "exists", return_value=True):
            config = load_config("config.yaml")

    # Verify merged configuration
    assert config["download"]["concurrent_downloads"] == 10
    assert config["download"]["retry_attempts"] == 5
    assert config["output"]["default_filename"] == "custom.pdf"
    assert config["output"]["download_dir"] == "downloaded_pdfs"  # Default value
    assert config["url"]["president"] == "biden"
    assert config["url"]["year"] == "2023"


def test_cli_help():
    """Test that CLI help message works."""
    runner = CliRunner()
    result = runner.invoke(cli, ["--help"])

    # Verify that the command executed successfully
    assert result.exit_code == 0
    # Check for expected help text
    assert (
        "First checks for missing PDFs and downloads them, then merges all PDFs."
        in result.output
    )


@patch("executive_orders_pdf.cli.download_and_merge")
@patch("executive_orders_pdf.cli.asyncio.run")
def test_cli_with_url(mock_run, mock_main):
    """Test CLI with direct URL argument."""

    # Create a NON-coroutine function for main to return
    def dummy_func(*args, **kwargs):
        return None

    # Return our dummy function instead of a coroutine
    mock_main.return_value = dummy_func

    # Configure mock_run to return a simple value
    mock_run.return_value = None

    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "https://example.com/orders",
            "--output",
            "output.pdf",
            "--download-dir",
            "downloads",
            "--concurrent-downloads",
            "3",
        ],
    )

    # Verify that the command executed successfully
    assert result.exit_code == 0

    # Verify that mock_main was called with the right parameters
    mock_main.assert_called_once_with(
        "https://example.com/orders", Path("output.pdf"), Path("downloads"), 3
    )

    # Verify asyncio.run was called
    mock_run.assert_called_once()


@patch("executive_orders_pdf.cli.download_and_merge")
@patch("executive_orders_pdf.cli.asyncio.run")
@patch("executive_orders_pdf.cli.load_config")
def test_cli_with_president_and_year(mock_load_config, mock_run, mock_main):
    """Test CLI with president and year options."""
    # Mock the config to return default values
    mock_load_config.return_value = {
        "download": {"concurrent_downloads": 5},
        "output": {"download_dir": "downloads", "default_filename": "default.pdf"},
        "url": {
            "base_url": "https://www.federalregister.gov/presidential-documents/executive-orders"
        },
    }

    # Create a NON-coroutine function for main to return
    def dummy_func(*args, **kwargs):
        return None

    # Return our dummy function instead of a coroutine
    mock_main.return_value = dummy_func

    # Configure mock_run to return a simple value
    mock_run.return_value = None

    runner = CliRunner()
    result = runner.invoke(cli, ["--president", "biden", "--year", "2023"])

    # Verify that the command executed successfully
    assert result.exit_code == 0

    # Verify that mock_main was called with correct URL
    expected_url = "https://www.federalregister.gov/presidential-documents/executive-orders/biden/2023"
    mock_main.assert_called_once()
    args, kwargs = mock_main.call_args
    assert args[0] == expected_url


@patch("executive_orders_pdf.cli.download_and_merge")
@patch("executive_orders_pdf.cli.asyncio.run")
@patch("executive_orders_pdf.cli.load_config")
def test_cli_with_config_file(mock_load_config, mock_run, mock_main):
    """Test CLI with a config file."""
    # Mock the config that would be loaded
    mock_load_config.return_value = {
        "download": {"concurrent_downloads": 10},
        "output": {
            "download_dir": "config_downloads",
            "default_filename": "from_config.pdf",
        },
        "url": {
            "base_url": "https://www.federalregister.gov/presidential-documents/executive-orders",
            "president": "config-president",
            "year": "2024",
        },
    }

    # Create a NON-coroutine function for main to return
    def dummy_func(*args, **kwargs):
        return None

    # Return our dummy function instead of a coroutine
    mock_main.return_value = dummy_func

    # Configure mock_run to return a simple value
    mock_run.return_value = None

    runner = CliRunner()
    result = runner.invoke(cli, ["--config", "config.yaml"])

    # Verify that the command executed successfully
    assert result.exit_code == 0

    # Verify load_config was called with the right file
    mock_load_config.assert_called_once_with("config.yaml")

    # Verify that mock_main was called with correct params
    expected_url = "https://www.federalregister.gov/presidential-documents/executive-orders/config-president/2024"
    # When using config file, the output filename comes from config, not auto-generated
    expected_filename = "from_config.pdf"

    mock_main.assert_called_once()
    args, kwargs = mock_main.call_args
    assert args[0] == expected_url
    assert args[1] == Path(expected_filename)
    assert args[2] == Path("config_downloads")
    assert args[3] == 10
