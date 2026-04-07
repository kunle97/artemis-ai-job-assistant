"""
Resume parser.

Extracts raw text from uploaded resume files and returns a lightweight
structured parsing result. This module currently supports PDF, DOCX,
and TXT files.
"""

from __future__ import annotations

import os
from pathlib import Path

from docx import Document
from pypdf import PdfReader


class ResumeParser:
    """
    Extracts text from supported resume file types.
    """

    SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".txt"}

    def parse(self, file_path: str) -> dict:
        """
        Parse a resume file and return extracted text plus lightweight metadata.
        """
        path = Path(file_path)
        extension = path.suffix.lower()

        if extension not in self.SUPPORTED_EXTENSIONS:
            return {
                "extracted_text": None,
                "parsed_json": {
                    "status": "unsupported_file_type",
                    "file_name": path.name,
                    "file_extension": extension,
                },
            }

        extracted_text = self._extract_text(path)

        return {
            "extracted_text": extracted_text,
            "parsed_json": {
                "status": "text_extracted" if extracted_text else "no_text_extracted",
                "file_name": path.name,
                "file_extension": extension,
                "character_count": len(extracted_text) if extracted_text else 0,
            },
        }

    def _extract_text(self, path: Path) -> str | None:
        """
        Route extraction to the correct file-type handler.
        """
        extension = path.suffix.lower()

        if extension == ".pdf":
            return self._extract_pdf_text(path)

        if extension == ".docx":
            return self._extract_docx_text(path)

        if extension == ".txt":
            return self._extract_txt_text(path)

        return None

    def _extract_pdf_text(self, path: Path) -> str | None:
        """
        Extract text from a PDF file using pypdf.
        """
        try:
            reader = PdfReader(str(path))
            pages: list[str] = []

            for page in reader.pages:
                page_text = page.extract_text() or ""
                if page_text.strip():
                    pages.append(page_text.strip())

            return "\n\n".join(pages) if pages else None
        except Exception as exc:
            return self._build_error_text(path, exc)

    def _extract_docx_text(self, path: Path) -> str | None:
        """
        Extract text from a DOCX file using python-docx.
        """
        try:
            document = Document(str(path))
            paragraphs = [
                paragraph.text.strip()
                for paragraph in document.paragraphs
                if paragraph.text and paragraph.text.strip()
            ]
            return "\n".join(paragraphs) if paragraphs else None
        except Exception as exc:
            return self._build_error_text(path, exc)

    def _extract_txt_text(self, path: Path) -> str | None:
        """
        Extract text from a plain text file.
        """
        try:
            return path.read_text(encoding="utf-8").strip() or None
        except UnicodeDecodeError:
            try:
                return path.read_text(encoding="latin-1").strip() or None
            except Exception as exc:
                return self._build_error_text(path, exc)
        except Exception as exc:
            return self._build_error_text(path, exc)

    def _build_error_text(self, path: Path, exc: Exception) -> str:
        """
        Return a small error marker string for debugging during development.

        This keeps failures visible in the DB while the parsing pipeline is still evolving.
        """
        return f"[PARSER_ERROR] Failed to extract text from {os.path.basename(path)}: {exc}"