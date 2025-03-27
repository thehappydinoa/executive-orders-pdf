"""Setup configuration for executive-orders-pdf."""

from setuptools import find_packages, setup

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [
        line.strip() for line in fh if line.strip() and not line.startswith("#")
    ]

with open("requirements-dev.txt", "r", encoding="utf-8") as fh:
    dev_requirements = [
        line.strip()
        for line in fh
        if line.strip() and not line.startswith("#") and not line.startswith("-r")
    ]


setup(
    name="executive-orders-pdf",
    version="0.1.0",
    author="Aidan Holland",
    author_email="thehappydinoa@gmail.com",
    description="A tool to download and merge executive order PDFs from the Federal Register",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/thehappydinoa/executive-orders-pdf",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    extras_require={"dev": dev_requirements},
    entry_points={
        "console_scripts": [
            "executive-orders-pdf=executive_orders_pdf.cli:cli",
            "pdf-summary=executive_orders_pdf.scripts.pdf_summary:main",
            "update-readme=executive_orders_pdf.scripts.update_readme:main",
        ],
    },
)
