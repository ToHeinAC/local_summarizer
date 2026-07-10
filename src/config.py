"""Environment/config loading. Plain python, no LangChain."""

from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Config:
    ollama_host: str
    app_port: int
    default_model: str
    default_template: str
    default_language: str
    ocr_model: str
    rewrite_model: str
    pdf_dpi: int


def load_config() -> Config:
    """Read config from the environment, applying sensible defaults."""
    return Config(
        ollama_host=os.getenv("OLLAMA_HOST", "http://localhost:11434"),
        app_port=int(os.getenv("APP_PORT", "8530")),
        default_model=os.getenv("DEFAULT_MODEL", "standard"),
        default_template=os.getenv("DEFAULT_TEMPLATE", "standard"),
        default_language=os.getenv("DEFAULT_LANGUAGE", "auto"),
        ocr_model=os.getenv("OCR_MODEL", "deepseek-ocr:3b"),
        rewrite_model=os.getenv("REWRITE_MODEL", "gemma4:e4b"),
        pdf_dpi=int(os.getenv("PDF_DPI", "150")),
    )
