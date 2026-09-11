"""Text extraction from CV files (PDF, DOCX, TXT)."""

from __future__ import annotations

from pathlib import Path

SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".txt"}


class ExtractionError(RuntimeError):
    pass


def extract_text(file_path: str) -> str:
    path = Path(file_path)
    if not path.exists():
        raise ExtractionError(f"File does not exist: {file_path}")
    if not path.is_file():
        raise ExtractionError(f"Not a file: {file_path}")

    ext = path.suffix.lower()
    if ext not in SUPPORTED_EXTENSIONS:
        raise ExtractionError(
            f"Unsupported extension {ext!r}. Supported: {sorted(SUPPORTED_EXTENSIONS)}"
        )

    if ext == ".pdf":
        return _extract_pdf(path)
    if ext == ".docx":
        return _extract_docx(path)
    return _extract_txt(path)


def _extract_pdf(path: Path) -> str:
    try:
        from pypdf import PdfReader
    except ImportError as exc:  # pragma: no cover
        raise ExtractionError("pypdf is not installed.") from exc

    reader = PdfReader(str(path))
    pages = [page.extract_text() or "" for page in reader.pages]
    text = "\n".join(pages).strip()
    if not text:
        raise ExtractionError("No text could be extracted from the PDF.")
    return text


def _extract_docx(path: Path) -> str:
    try:
        from docx import Document
    except ImportError as exc:  # pragma: no cover
        raise ExtractionError("python-docx is not installed.") from exc

    document = Document(str(path))
    text = "\n".join(p.text for p in document.paragraphs).strip()
    if not text:
        raise ExtractionError("No text could be extracted from the DOCX.")
    return text


def _extract_txt(path: Path) -> str:
    text = path.read_text(encoding="utf-8", errors="replace").strip()
    if not text:
        raise ExtractionError("File is empty.")
    return text
