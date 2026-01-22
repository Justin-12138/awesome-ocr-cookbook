# Awesome OCR Cookbook

A collection of practical recipes and implementation examples for famous OCR (Optical Character Recognition) models.

## Overview

This project provides ready-to-use implementations for various OCR models, making it easy to integrate state-of-the-art text extraction capabilities into your applications. Each cookbook contains a complete, production-ready pipeline with error handling, concurrency support, and clear documentation.

## Features

- **Multiple OCR Models**: Support for various OCR engines and vision-language models
- **Production-Ready**: Robust error handling, retry mechanisms, and timeout management
- **Concurrent Processing**: Multi-threaded processing for improved performance
- **PDF Support**: Direct PDF document processing with page-by-page extraction
- **Flexible Output**: Multiple output formats including clean text and page-separated versions

## Installation

### Requirements

- Python 3.12 or higher

### Setup

1. Clone the repository:
```bash
git clone https://github.com/yourusername/awesome-ocr-cookbook.git
cd awesome-ocr-cookbook
```

2. Install dependencies using your preferred package manager:

**Using uv (recommended):**
```bash
uv pip install -e .
```

**Using pip:**
```bash
pip install -e .
```

3. Install model-specific dependencies (see individual cookbook sections below)

## Supported OCR Models

### LightOnOCR

The [LightOnOCR-2-1B](https://github.com/lightonai/lighton-ocr) model is a vision-language model that excels at text extraction from images.

#### Installation

```bash
pip install pypdfium2 requests
```

#### Usage

```python
from cookbooks.pipeline_lightonocr import pdf_to_md

# Convert PDF to Markdown
pdf_to_md(
    pdf_path="path/to/your/document.pdf",
    output_md_path="path/to/output.md"
)
```

This will generate two output files:
- `output.md` - Clean concatenated text
- `output_with_separators.md` - Text with page separators (## Page N)

#### Configuration

Edit the constants in [cookbooks/pipeline_lightonocr.py](cookbooks/pipeline_lightonocr.py):

```python
ENDPOINT = "http://localhost:9090/v1/chat/completions"  # Your OCR API endpoint
MODEL = "LightOnOCR-2-1B"                               # Model name
MAX_WORKERS = 8                                         # Concurrent threads
REQUEST_TIMEOUT = 120                                   # Request timeout (seconds)
```

## Project Structure

```
awesome-ocr-cookbook/
├── cookbooks/              # OCR model implementations
│   └── pipeline_lightonocr.py
├── assets/                 # Static assets
├── pdf/                    # Sample PDF files
├── main.py                 # Main entry point
├── pyproject.toml          # Project configuration
└── README.md               # This file
```

## Development

### Adding a New OCR Model

1. Create a new file in the `cookbooks/` directory named `pipeline_<model_name>.py`
2. Implement your OCR pipeline following these patterns:
   - Use `requests.Session` with connection pooling
   - Implement proper error handling and retries
   - Add type hints and docstrings
   - Include example usage

Example template:
```python
"""
OCR pipeline for <Model Name>
"""
import requests
from pathlib import Path

def ocr_image(image_path: str) -> str:
    """Extract text from an image using <Model Name>"""
    # Implementation here
    pass

def pdf_to_md(pdf_path: str, output_md_path: str) -> None:
    """Convert PDF to Markdown using <Model Name>"""
    # Implementation here
    pass
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Roadmap

- [ ] Add Tesseract OCR cookbook
- [ ] Add PaddleOCR cookbook
- [ ] Add EasyOCR cookbook
- [ ] Add more example files and test cases
- [ ] Add unit tests
- [ ] Add CLI interface

## Acknowledgments

- [LightOnAI](https://github.com/lightonai/lighton-ocr) for the LightOnOCR model
- All OCR model developers and contributors
