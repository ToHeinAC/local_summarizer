import pytest

from src.extract import UnsupportedFileError, extract_text


def test_extract_txt(txt_bytes):
    assert "revenue" in extract_text("report.txt", txt_bytes)


def test_extract_md(md_bytes):
    text = extract_text("report.md", md_bytes)
    assert "Report" in text and "revenue" in text


def test_extract_docx(docx_bytes):
    assert "European market" in extract_text("report.docx", docx_bytes)


def test_extract_pdf(pdf_bytes):
    assert "revenue" in extract_text("report.pdf", pdf_bytes)


def test_extension_is_case_insensitive(txt_bytes):
    assert extract_text("REPORT.TXT", txt_bytes)


def test_unsupported_extension_raises(txt_bytes):
    with pytest.raises(UnsupportedFileError):
        extract_text("report.rtf", txt_bytes)


def test_no_extension_raises(txt_bytes):
    with pytest.raises(UnsupportedFileError):
        extract_text("report", txt_bytes)


def test_output_is_stripped(txt_bytes):
    text = extract_text("report.txt", b"  \n" + txt_bytes + b"\n  ")
    assert text == text.strip()
