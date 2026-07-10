"""LLM registry and Ollama availability check. Plain python, no LangChain.

Each model exposes an Ollama tag plus human-facing capability/perf metrics
shown in the UI. ``label`` and ``note`` are per-GUI-language dicts; read them
with ``i18n.pick``. ``installed_tags`` queries the local Ollama server so the UI
can warn about models that are not pulled yet.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request

# id -> registry entry. Tags match the PRD and the user's local `ollama list`.
MODELS: list[dict] = [
    {
        "id": "fast",
        "tag": "gemma4:e2b",
        "label": {"de": "Schnell (gemma4:e2b)", "en": "Fast (gemma4:e2b)"},
        "speed": 3,
        "quality": 1,
        "note": {
            "de": "Geringste Latenz; gut für schnelle Entwürfe.",
            "en": "Lowest latency; good for quick drafts.",
        },
    },
    {
        "id": "standard",
        "tag": "gemma4:e4b",
        "label": {"de": "Standard (gemma4:e4b)", "en": "Standard (gemma4:e4b)"},
        "speed": 2,
        "quality": 2,
        "note": {"de": "Ausgewogene Voreinstellung.", "en": "Balanced default."},
    },
    {
        "id": "smarter",
        "tag": "qwen3:14b",
        "label": {"de": "Klüger (qwen3:14b)", "en": "Smarter (qwen3:14b)"},
        "speed": 1,
        "quality": 3,
        "note": {
            "de": "Stärkere Schlussfolgerungen; langsamer.",
            "en": "Stronger reasoning; slower.",
        },
    },
    {
        "id": "accurate",
        "tag": "gpt-oss:20b",
        "label": {"de": "Genau (gpt-oss:20b)", "en": "Accurate (gpt-oss:20b)"},
        "speed": 1,
        "quality": 3,
        "note": {"de": "Höchste Genauigkeit; am langsamsten.", "en": "Highest fidelity; slowest."},
    },
]

DEFAULT_MODEL_ID = "standard"


def list_models() -> list[dict]:
    """Return all registered models."""
    return MODELS


def get_model(model_id: str) -> dict:
    """Return the registry entry for ``model_id``; raise KeyError if unknown."""
    for model in MODELS:
        if model["id"] == model_id:
            return model
    raise KeyError(f"Unknown model id: {model_id}")


def installed_tags(host: str, timeout: float = 2.0) -> set[str]:
    """Return the set of model tags installed on the Ollama server.

    Returns an empty set if the server is unreachable.
    """
    url = host.rstrip("/") + "/api/tags"
    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, OSError, ValueError):
        return set()
    return {model.get("name", "") for model in payload.get("models", [])}


def annotate_availability(host: str) -> list[dict]:
    """Return models with an ``installed`` bool based on the Ollama server."""
    tags = installed_tags(host)
    return [{**model, "installed": model["tag"] in tags} for model in MODELS]
