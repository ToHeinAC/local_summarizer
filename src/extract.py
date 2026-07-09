"""Extract plain text from uploaded files. Plain python, no LangChain.

Supported: .pdf, .docx, .txt, .md
"""

from __future__ import annotations

import io

from docx import Document
from pypdf import PdfReader

SUPPORTED_EXTENSIONS = (".pdf", ".docx", ".txt", ".md")


class UnsupportedFileError(ValueError):
    """Raised when a file's extension is not supported."""


def _extension(filename: str) -> str:
    dot = filename.rfind(".")
    return filename[dot:].lower() if dot != -1 else ""


def _extract_pdf(data: bytes) -> str:
    reader = PdfReader(io.BytesIO(data))
    return "\n".join(page.extract_text() or "" for page in reader.pages)


def _extract_docx(data: bytes) -> str:
    document = Document(io.BytesIO(data))
    return "\n".join(p.text for p in document.paragraphs)


def _extract_text(data: bytes) -> str:
    return data.decode("utf-8", errors="replace")


def extract_text(filename: str, data: bytes) -> str:
    """Return the plain text of ``data`` based on ``filename``'s extension.

    Raises UnsupportedFileError for unknown extensions.
    """
    ext = _extension(filename)
    if ext == ".pdf":
        text = _extract_pdf(data)
    elif ext == ".docx":
        text = _extract_docx(data)
    elif ext in (".txt", ".md"):
        text = _extract_text(data)
    else:
        raise UnsupportedFileError(
            f"Unsupported file type '{ext or filename}'. "
            f"Supported: {', '.join(SUPPORTED_EXTENSIONS)}"
        )
    return text.strip()
