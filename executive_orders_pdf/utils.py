"""Common utility functions and classes used across the project."""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from pypdf import PdfReader, PdfWriter
from rich.console import Console
from rich.progress import Progress

# Initialize console for consistent output
console = Console()


class PDFUtils:
    """Common PDF-related utility functions."""

    @staticmethod
    def get_pdf_info(pdf_path: Path) -> Optional[Dict]:
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
            stats = pdf_path.stat()
            size_mb = stats.st_size / (1024 * 1024)
            last_modified = datetime.fromtimestamp(stats.st_mtime).strftime(
                "%Y-%m-%d %H:%M:%S"
            )

            # Parse filename to get president and year
            filename = pdf_path.name
            president = "Unknown"
            year = "Unknown"

            parts = filename.replace(".pdf", "").split("_")
            if len(parts) >= 3:
                president = parts[0].replace("-", " ").title()
                year = parts[-1]

            return {
                "filename": filename,
                "base_filename": filename,
                "president": president,
                "year": year,
                "pages": num_pages,
                "size_mb": round(size_mb, 2),
                "last_modified": last_modified,
            }
        except Exception as e:
            console.print(f"[red]Error processing {pdf_path}: {str(e)}[/red]")
            return None

    @staticmethod
    def clean_pdf_for_deterministic_output(pdf_path: Path) -> PdfWriter:
        """
        Clean a PDF to make it more deterministic by removing metadata.

        Args:
            pdf_path: Path to the PDF file

        Returns:
            PdfWriter with cleaned PDF content
        """
        reader = PdfReader(pdf_path)
        writer = PdfWriter()

        # Copy pages without any metadata
        for page in reader.pages:
            writer.add_page(page)

        # First compress identical objects, then remove metadata
        writer.compress_identical_objects(remove_identicals=True, remove_orphans=True)
        writer.metadata = None

        return writer

    @staticmethod
    def verify_pdf(file_path: Path) -> bool:
        """
        Verify that a PDF is valid and not corrupted.

        Args:
            file_path: Path to the PDF file

        Returns:
            bool: True if PDF is valid, False otherwise
        """
        try:
            reader = PdfReader(file_path)
            _ = len(reader.pages)
            return True
        except Exception as e:
            console.print(
                f"[red]PDF verification failed for {file_path}: {str(e)}[/red]"
            )
            return False


class FileSystemUtils:
    """Common filesystem-related utility functions."""

    @staticmethod
    def ensure_directory(directory: Path) -> None:
        """
        Ensure a directory exists, create if it doesn't.

        Args:
            directory: Path to the directory
        """
        directory.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def move_files_to_directory(files: List[Path], target_dir: Path) -> List[Path]:
        """
        Move files to a target directory.

        Args:
            files: List of file paths to move
            target_dir: Target directory path

        Returns:
            List of new file paths after moving
        """
        moved_files = []
        for file_path in files:
            target_path = target_dir / file_path.name
            console.print(f"[yellow]Moving {file_path} to {target_path}[/yellow]")
            file_path.rename(target_path)
            moved_files.append(target_path)
        return moved_files


class ConfigUtils:
    """Common configuration-related utility functions."""

    @staticmethod
    def load_json_config(config_path: Path) -> Dict:
        """
        Load configuration from a JSON file.

        Args:
            config_path: Path to the JSON config file

        Returns:
            Dictionary with configuration
        """
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            console.print(
                f"[yellow]Warning: Config file {config_path} not found[/yellow]"
            )
            return {}
        except json.JSONDecodeError:
            console.print(f"[red]Error: Invalid JSON in {config_path}[/red]")
            return {}

    @staticmethod
    def save_json_config(config: Dict, config_path: Path) -> None:
        """
        Save configuration to a JSON file.

        Args:
            config: Dictionary with configuration
            config_path: Path to save the JSON config file
        """
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2)


class ProgressTracker:
    """Common progress tracking functionality."""

    def __init__(self, total: int, description: str = "Processing"):
        """
        Initialize progress tracker.

        Args:
            total: Total number of items to process
            description: Description of the progress task
        """
        self.progress = Progress()
        self.task_id = self.progress.add_task(f"[cyan]{description}...", total=total)

    def update(self, advance: int = 1) -> None:
        """
        Update progress.

        Args:
            advance: Number of items processed
        """
        if self.progress:
            self.progress.update(self.task_id, advance=advance)

    def __enter__(self):
        """Context manager entry."""
        self.progress.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.progress.stop()
