import pytest

from src.extract import UnsupportedFileError, to_markdown


def test_txt_passes_through(txt_bytes):
    assert "revenue" in to_markdown("report.txt", txt_bytes)


def test_md_passes_through(md_bytes):
    text = to_markdown("report.md", md_bytes)
    assert "# Report" in text and "revenue" in text


def test_docx_becomes_markdown(docx_bytes):
    assert "European market" in to_markdown("report.docx", docx_bytes)


def test_pdf_with_text_layer_is_rewritten(pdf_bytes, stub_ollama):
    text = to_markdown("report.pdf", pdf_bytes)
    assert "revenue" in text
    assert stub_ollama.rewritten, "a text-layer page must go through the rewrite model"
    assert not stub_ollama.ocr_prompts, "a text-layer page must not be OCR'd"


def test_scanned_pdf_is_ocred(scanned_pdf_bytes, stub_ollama):
    text = to_markdown("scan.pdf", scanned_pdf_bytes)
    assert "revenue" in text
    assert stub_ollama.ocr_prompts, "a page without a text layer must be OCR'd"
    assert not stub_ollama.rewritten


def test_extension_is_case_insensitive(txt_bytes):
    assert to_markdown("REPORT.TXT", txt_bytes)


def test_unsupported_extension_raises(txt_bytes):
    with pytest.raises(UnsupportedFileError):
        to_markdown("report.rtf", txt_bytes)


def test_no_extension_raises(txt_bytes):
    with pytest.raises(UnsupportedFileError):
        to_markdown("report", txt_bytes)


def test_output_is_stripped(txt_bytes):
    text = to_markdown("report.txt", b"  \n" + txt_bytes + b"\n  ")
    assert text == text.strip()
