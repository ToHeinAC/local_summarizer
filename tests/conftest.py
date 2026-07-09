"""Shared fixtures: tiny in-memory documents and a fake LLM."""

from __future__ import annotations

import io

import pytest
from docx import Document
from fpdf import FPDF

SAMPLE_TEXT = (
    "The quarterly report shows revenue of 4.2 million dollars. "
    "Growth was driven by the European market. "
    "The board approved a new budget for research."
)


@pytest.fixture
def txt_bytes() -> bytes:
    return SAMPLE_TEXT.encode("utf-8")


@pytest.fixture
def md_bytes() -> bytes:
    return f"# Report\n\n{SAMPLE_TEXT}\n".encode("utf-8")


@pytest.fixture
def docx_bytes() -> bytes:
    document = Document()
    for sentence in SAMPLE_TEXT.split(". "):
        document.add_paragraph(sentence)
    buffer = io.BytesIO()
    document.save(buffer)
    return buffer.getvalue()


@pytest.fixture
def pdf_bytes() -> bytes:
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", size=12)
    pdf.multi_cell(0, 10, SAMPLE_TEXT)
    return bytes(pdf.output())


@pytest.fixture
def scanned_pdf_bytes() -> bytes:
    """A PDF whose page carries no text layer -> must take the OCR path."""
    pdf = FPDF()
    pdf.add_page()
    return bytes(pdf.output())


class StubOllama:
    """Records md_convert's Ollama calls so ingestion stays offline."""

    def __init__(self) -> None:
        self.rewritten: list[str] = []
        self.ocr_prompts: list[str] = []
        self.unloaded: list[str] = []

    def rewrite(self, model_id, prompt, host=None):
        self.rewritten.append(prompt)
        return "# Rewritten\n\nrevenue of 4.2 million dollars"

    def ocr(self, model_id, prompt, image_b64, host=None):
        self.ocr_prompts.append(prompt)
        return "# Scanned\n\nrevenue of 4.2 million dollars"

    def unload(self, model_id, host=None):
        self.unloaded.append(model_id)


@pytest.fixture
def stub_ollama(monkeypatch) -> StubOllama:
    from src import ollama_client

    stub = StubOllama()
    for name in ("rewrite", "ocr", "unload"):
        monkeypatch.setattr(ollama_client, name, getattr(stub, name))
    return stub


class FakeLLM:
    """Minimal stand-in for ChatOllama: echoes a canned response."""

    def __init__(self, response: str = "FAKE SUMMARY"):
        self.response = response
        self.calls: list[str] = []

    def invoke(self, prompt: str):
        self.calls.append(prompt)

        class _Msg:
            content = self.response

        return _Msg()


@pytest.fixture
def fake_llm() -> FakeLLM:
    return FakeLLM()
