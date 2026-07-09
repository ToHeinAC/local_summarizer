"""Detect the main language of a document. Plain python, no LangChain."""

from __future__ import annotations

from langdetect import DetectorFactory, LangDetectException, detect

# Make detection deterministic across runs.
DetectorFactory.seed = 0


def detect_language(text: str, fallback: str = "en") -> str:
    """Return an ISO-639-1 code for ``text``'s main language.

    Returns ``fallback`` for empty input or when detection fails.
    """
    if not text or not text.strip():
        return fallback
    try:
        return detect(text)
    except LangDetectException:
        return fallback
