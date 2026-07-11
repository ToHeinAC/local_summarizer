"""Turn uploaded files into Markdown. Plain python, no LangChain.

Every supported format becomes Markdown before summarization:

- ``.md`` / ``.txt`` are already text and pass through unchanged.
- ``.docx`` is mapped deterministically (headings, lists, tables).
- ``.pdf`` is routed per page — text pages are LLM-rewritten, scanned pages OCR'd.

See :mod:`src.md_convert` for the PDF/DOCX conversion itself.
"""

from __future__ import annotations

from src import md_convert
from src.i18n import DEFAULT_LANG, t
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
    rewrite_model: str = "LiquidAI/lfm2.5-1.2b-instruct:latest",
    dpi: int = 150,
    host: str | None = None,
    on_progress: ProgressCb | None = None,
    lang: str = DEFAULT_LANG,
    fast: bool = False,
) -> str:
    """Return the Markdown of ``data`` based on ``filename``'s extension.

    ``lang`` is the GUI language of the progress labels and the error message.
    ``fast=True`` skips the per-page LLM rewrite for digital PDF pages (see
    :func:`md_convert.pdf_to_markdown`). Raises UnsupportedFileError for unknown
    extensions.
    """
    ext = _extension(filename)
    if ext == ".pdf":
        text = md_convert.pdf_to_markdown(
            data, ocr_model, rewrite_model, dpi, host, on_progress, lang, fast
        )
    elif ext == ".docx":
        text = md_convert.docx_to_markdown(data)
    elif ext in (".txt", ".md"):
        text = data.decode("utf-8", errors="replace")
    else:
        raise UnsupportedFileError(
            t(
                "unsupported_file",
                lang,
                ext=ext or filename,
                supported=", ".join(SUPPORTED_EXTENSIONS),
            )
        )
    return text.strip()
