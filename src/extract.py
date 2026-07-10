"""Turn uploaded files into Markdown. Plain python, no LangChain.

Every supported format becomes Markdown before summarization:

- ``.md`` / ``.txt`` are already text and pass through unchanged.
- ``.docx`` is mapped deterministically (headings, lists, tables).
- ``.pdf`` is routed per page — text pages are LLM-rewritten, scanned pages OCR'd.

See :mod:`src.md_convert` for the PDF/DOCX conversion itself.
"""

from __future__ import annotations

from src import md_convert
from src.md_convert import ProgressCb

SUPPORTED_EXTENSIONS = (".pdf", ".docx", ".txt", ".md")


class UnsupportedFileError(ValueError):
    """Raised when a file's extension is not supported."""


def _extension(filename: str) -> str:
    dot = filename.rfind(".")
    return filename[dot:].lower() if dot != -1 else ""


def to_markdown(
    filename: str,
    data: bytes,
    *,
    ocr_model: str = "deepseek-ocr:3b",
    rewrite_model: str = "gemma4:e4b",
    dpi: int = 150,
    host: str | None = None,
    on_progress: ProgressCb | None = None,
) -> str:
    """Return the Markdown of ``data`` based on ``filename``'s extension.

    Raises UnsupportedFileError for unknown extensions.
    """
    ext = _extension(filename)
    if ext == ".pdf":
        text = md_convert.pdf_to_markdown(
            data, ocr_model, rewrite_model, dpi, host, on_progress
        )
    elif ext == ".docx":
        text = md_convert.docx_to_markdown(data)
    elif ext in (".txt", ".md"):
        text = data.decode("utf-8", errors="replace")
    else:
        raise UnsupportedFileError(
            f"Nicht unterstützter Dateityp '{ext or filename}'. "
            f"Unterstützt: {', '.join(SUPPORTED_EXTENSIONS)}"
        )
    return text.strip()
