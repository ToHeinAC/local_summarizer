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
