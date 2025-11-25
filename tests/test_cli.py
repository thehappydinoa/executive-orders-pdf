"""Tests for the CLI module."""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

# Import the cli functions - using a try/except to handle potential import issues
try:
    from executive_orders_pdf.cli import cli, load_config

    # Get the actual module object using sys.modules
    cli_module = sys.modules["executive_orders_pdf.cli"]
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


def test_cli_with_url():
    """Test CLI with direct URL argument."""
    with patch.object(cli_module, "download_and_merge"):
        with patch.object(cli_module, "asyncio") as mock_asyncio:
            # Configure mock_run to return a simple value
            mock_asyncio.run.return_value = None

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

            # Verify asyncio.run was called
            mock_asyncio.run.assert_called_once()


def test_cli_with_president_and_year():
    """Test CLI with president and year options."""
    with patch.object(cli_module, "load_config") as mock_load_config:
        with patch.object(cli_module, "download_and_merge"):
            with patch.object(cli_module, "asyncio") as mock_asyncio:
                # Mock the config to return default values
                mock_load_config.return_value = {
                    "download": {"concurrent_downloads": 5},
                    "output": {
                        "download_dir": "downloads",
                        "default_filename": "default.pdf",
                    },
                    "url": {
                        "base_url": "https://www.federalregister.gov/presidential-documents/executive-orders"
                    },
                }

                # Configure mock_run to return a simple value
                mock_asyncio.run.return_value = None

                runner = CliRunner()
                result = runner.invoke(cli, ["--president", "biden", "--year", "2023"])

                # Verify that the command executed successfully
                assert result.exit_code == 0

                # Verify asyncio.run was called
                mock_asyncio.run.assert_called_once()


def test_cli_with_config_file():
    """Test CLI with a config file."""
    with patch.object(cli_module, "load_config") as mock_load_config:
        with patch.object(cli_module, "download_and_merge"):
            with patch.object(cli_module, "asyncio") as mock_asyncio:
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

                # Configure mock_run to return a simple value
                mock_asyncio.run.return_value = None

                runner = CliRunner()
                result = runner.invoke(cli, ["--config", "config.yaml"])

                # Verify that the command executed successfully
                assert result.exit_code == 0

                # Verify load_config was called with the right file
                mock_load_config.assert_called_once_with("config.yaml")

                # Verify asyncio.run was called
                mock_asyncio.run.assert_called_once()
