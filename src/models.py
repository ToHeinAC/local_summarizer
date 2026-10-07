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
        "tag": "LiquidAI/lfm2.5-1.2b-instruct:latest",
        "label": {
            "de": "Schnell (lfm2.5-1.2b-instruct)",
            "en": "Fast (lfm2.5-1.2b-instruct)",
        },
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
    {
        "id": "qwen38",
        "tag": "qwen3.8-27b:latest",
        "label": {"de": "Qwen3.8 (27B)", "en": "Qwen3.8 (27B)"},
        "speed": 1,
        "quality": 3,
        "note": {
            "de": "Größtes Modell (27B); GPU-gepinnt am schnellsten.",
            "en": "Largest model (27B); fastest when GPU-pinned.",
        },
    },
    {
        "id": "hybrid",
        "tag": "qwen3.8-27b:latest",  # final summary (finalize node)
        "map_tag": "gemma4:e4b",  # per-chunk map + reduce passes
        "label": {
            "de": "Hybrid (gemma4:e4b + Qwen3.8 27B)",
            "en": "Hybrid (gemma4:e4b + Qwen3.8 27B)",
        },
        "speed": 2,
        "quality": 3,
        "note": {
            "de": "gemma4:e4b fasst die Abschnitte zusammen, Qwen3.8 schreibt nur die Endfassung.",
            "en": "gemma4:e4b summarizes the sections; Qwen3.8 writes only the final summary.",
        },
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


def model_tags(model: dict) -> list[str]:
    """Every Ollama tag ``model`` needs (the hybrid also needs its ``map_tag``)."""
    return [model["tag"], *([model["map_tag"]] if "map_tag" in model else [])]


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
    annotated = []
    for model in MODELS:
        missing = [t for t in model_tags(model) if t not in tags]
        annotated.append({**model, "installed": not missing, "missing": missing})
    return annotated
