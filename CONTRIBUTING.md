# Contributing to Executive Orders PDF Downloader

Thank you for your interest in contributing to this project! This document provides guidelines and instructions for contributing.

## Setting Up Development Environment

1. Clone the repository:
   ```bash
   git clone https://github.com/thehappydinoa/executive-orders-pdf.git
   cd executive-orders-pdf
   ```

2. Create and activate a virtual environment:
   ```bash
   # On Windows
   python -m venv venv
   .\venv\Scripts\activate

   # On macOS/Linux
   python -m venv venv
   source venv/bin/activate
   ```

3. Install development dependencies:
   ```bash
   pip install -r requirements-dev.txt
   ```

4. Set up pre-commit hooks:
   ```bash
   pre-commit install
   ```

## Code Style

This project uses:
- **Black** for code formatting
- **isort** for import sorting
- **flake8** with flake8-bugbear for linting

All of these run automatically when you commit, thanks to pre-commit hooks.

## Running Tests

Run the test suite using pytest:

```bash
pytest
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
