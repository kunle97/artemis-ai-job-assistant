"""
Resume parser.

Extracts raw text from uploaded resume files and returns lightweight
structured metadata. Supports PDF, DOCX, and TXT files.
"""

from pathlib import Path

from docx import Document
from pypdf import PdfReader

from src.domain.resume.normalizer import ResumeNormalizer


class ResumeParser:
    """
    Extracts text from supported resume file types and normalizes it into
    a lightweight structured representation.
    """

    SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".txt"}

    def __init__(self):
        self.normalizer = ResumeNormalizer()

    def parse(self, file_path: str) -> dict:
        """
        Parse a resume file and return extracted text plus structured metadata.
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
                    "normalized_data": None,
                },
            }

        extracted_text = self._extract_text(path)
        normalized_data = self.normalizer.normalize(extracted_text, file_path=file_path)

        return {
            "extracted_text": extracted_text,
            "parsed_json": {
                "status": "text_extracted" if extracted_text else "no_text_extracted",
                "file_name": path.name,
                "file_extension": extension,
                "character_count": len(extracted_text) if extracted_text else 0,
                "normalized_data": normalized_data,
            },
        }

    def _extract_text(self, path: Path) -> str | None:
        extension = path.suffix.lower()

        if extension == ".pdf":
            return self._extract_pdf_text(path)
        if extension == ".docx":
            return self._extract_docx_text(path)
        if extension == ".txt":
            return self._extract_txt_text(path)

        return None

    def _extract_pdf_text(self, path: Path) -> str | None:
        try:
            reader = PdfReader(str(path))
            pages: list[str] = []

            for page in reader.pages:
                page_text = page.extract_text() or ""
                if page_text.strip():
                    pages.append(page_text.strip())

            return "\n\n".join(pages) if pages else None
        except Exception as exc:
            return f"[PARSER_ERROR] PDF extraction failed: {exc}"

    def _extract_docx_text(self, path: Path) -> str | None:
        try:
            document = Document(str(path))
            paragraphs = [
                paragraph.text.strip()
                for paragraph in document.paragraphs
                if paragraph.text and paragraph.text.strip()
            ]
            return "\n".join(paragraphs) if paragraphs else None
        except Exception as exc:
            return f"[PARSER_ERROR] DOCX extraction failed: {exc}"

    def _extract_txt_text(self, path: Path) -> str | None:
        try:
            return path.read_text(encoding="utf-8").strip() or None
        except UnicodeDecodeError:
            try:
                return path.read_text(encoding="latin-1").strip() or None
            except Exception as exc:
                return f"[PARSER_ERROR] TXT extraction failed: {exc}"
        except Exception as exc:
            return f"[PARSER_ERROR] TXT extraction failed: {exc}"