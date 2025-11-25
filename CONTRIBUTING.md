# Contributing to Executive Orders PDF Downloader

Thank you for your interest in contributing to this project! This document provides guidelines and instructions for contributing.

## Setting Up Development Environment

1. Clone the repository:

   ```bash
   git clone https://github.com/thehappydinoa/executive-orders-pdf.git
   cd executive-orders-pdf
   ```

2. Install uv (if not already installed):

   ```bash
   # On macOS/Linux
   curl -LsSf https://astral.sh/uv/install.sh | sh

   # On Windows (PowerShell)
   powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
   ```

3. Install dependencies:

   ```bash
   uv sync --dev
   ```

4. Set up pre-commit hooks:

   ```bash
   uv run pre-commit install
   ```

## Code Style

This project uses:

- **Black** for code formatting
- **isort** for import sorting
- **flake8** with flake8-bugbear for linting
- **mypy** for type checking

All of these run automatically when you commit, thanks to pre-commit hooks.

## Running Tests

Run the test suite using pytest:

```bash
uv run pytest
```

With coverage:

```bash
uv run pytest --cov=executive_orders_pdf --cov-report=term-missing
```

## Pull Request Process

1. Fork the repository
2. Create a new branch for your feature or fix
3. Make your changes
4. Run the tests to ensure they pass
5. Submit a pull request

## Code of Conduct

Please be respectful and considerate of others when contributing to this project.

## License

By contributing to this project, you agree that your contributions will be licensed under the project's MIT License.
