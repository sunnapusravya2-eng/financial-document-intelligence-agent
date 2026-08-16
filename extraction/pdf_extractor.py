from io import BytesIO
from typing import List, Dict, Any

from PyPDF2 import PdfReader


def extract_pdf_text(pdf_bytes: bytes) -> List[Dict[str, Any]]:
    """Extract text from each page of a PDF.

    Returns a list of dictionaries with page_number and text.
    """
    if not pdf_bytes:
        raise ValueError("PDF file is empty.")

    pages: List[Dict[str, Any]] = []
    reader = PdfReader(BytesIO(pdf_bytes))

    if len(reader.pages) == 0:
        raise ValueError("No pages were found in this PDF.")

    for page_number, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        pages.append({
            "page_number": page_number,
            "text": text.strip(),
        })

    return pages
