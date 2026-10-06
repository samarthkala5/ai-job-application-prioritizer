"""PDF text extraction using PyMuPDF (fitz)."""

from __future__ import annotations

from pathlib import Path
from typing import Union, BinaryIO, Optional

try:
    import pymupdf as fitz
except ImportError:
    import fitz  # PyMuPDF


class PDFParser:
    """Extract plain text from PDF files using PyMuPDF."""

    def __init__(self) -> None:
        pass

    def extract_text(self, source: Union[str, Path, BinaryIO, bytes]) -> str:
        """Extract text from a PDF file.

        Args:
            source: File path, Path object, file-like object, or raw bytes.

        Returns:
            Extracted text as a string. Empty string if extraction fails.

        Raises:
            ValueError: If source is None or not a valid input type.
            FileNotFoundError: If file path does not exist.
        """
        if source is None:
            raise ValueError("Source cannot be None")

        if isinstance(source, (str, Path)):
            path = Path(source)
            if not path.exists():
                raise FileNotFoundError(f"File not found: {source}")
            if not path.is_file():
                raise ValueError(f"Path is not a file: {source}")

            with fitz.open(str(path)) as doc:
                return self._extract_from_document(doc)
        elif isinstance(source, bytes):
            with fitz.open(stream=source, filetype="pdf") as doc:
                return self._extract_from_document(doc)
        elif hasattr(source, "read"):
            data = source.read()
            if isinstance(data, bytes):
                with fitz.open(stream=data, filetype="pdf") as doc:
                    return self._extract_from_document(doc)
            else:
                raise ValueError("File-like object must return bytes")
        else:
            raise ValueError(f"Unsupported source type: {type(source)}")

    def extract_text_from_bytes(self, data: bytes) -> str:
        """Extract text from raw PDF bytes.

        Args:
            data: Raw PDF file content as bytes.

        Returns:
            Extracted text as a string.
        """
        with fitz.open(stream=data, filetype="pdf") as doc:
            return self._extract_from_document(doc)

    @staticmethod
    def _extract_from_document(doc: fitz.Document) -> str:
        """Extract text from all pages of a PyMuPDF document."""
        text_parts: list[str] = []
        for page in doc:
            page_text = page.get_text("text")
            if page_text:
                text_parts.append(page_text)
        return "\n".join(text_parts)


def parse_pdf(source: Union[str, Path, BinaryIO]) -> str:
    """Convenience function to extract text from a PDF file.

    Args:
        source: File path, Path object, or file-like object.

    Returns:
        Extracted text as a string.
    """
    parser = PDFParser()
    return parser.extract_text(source)