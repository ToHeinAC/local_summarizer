from src import export

SAMPLE = "## Overview\n\nRevenue rose.\n\n## Key Points\n\n- Point one\n- Point two\n"


def test_markdown_roundtrip():
    assert export.to_markdown(SAMPLE) == SAMPLE.encode("utf-8")


def test_docx_is_valid_zip():
    data = export.to_docx(SAMPLE)
    assert data[:2] == b"PK"  # docx is a zip container


def test_docx_contains_text():
    import io

    from docx import Document

    document = Document(io.BytesIO(export.to_docx(SAMPLE)))
    text = "\n".join(p.text for p in document.paragraphs)
    assert "Revenue rose." in text
    assert "Point one" in text


def test_pdf_has_header():
    data = export.to_pdf(SAMPLE)
    assert data[:4] == b"%PDF"
    assert len(data) > 500


def test_pdf_handles_unicode():
    # Should not raise even with non-latin characters.
    assert export.to_pdf("## Überblick\n\n- Ключевой пункт\n").startswith(b"%PDF")


def test_exporters_registry():
    assert set(export.EXPORTERS) == {"md", "docx", "pdf"}
    for mime, fn in export.EXPORTERS.values():
        assert isinstance(mime, str) and callable(fn)
