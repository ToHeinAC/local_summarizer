"""Direct Ollama calls for Markdown conversion. Plain python, no LangChain.

Used by ``md_convert`` for vision OCR and text rewriting. The agent layer keeps
using ``langchain-ollama`` via ``tools.py``; this module exists so the ingestion
layer can reach Ollama without importing LangChain.
"""

from __future__ import annotations

from ollama import Client

# Cap the KV-cache context so Ollama does not allocate each model's full trained
# window (128k+), which balloons VRAM and cuts throughput ~5x. One PDF page of
# text (or its rasterized image tokens) fits comfortably; OCR gets extra
# headroom for image tokens plus a long transcription.
REWRITE_NUM_CTX = 8192
OCR_NUM_CTX = 16384


def _client(host: str | None = None) -> Client:
    return Client(host=host) if host else Client()


def ocr(model_id: str, prompt: str, image_b64: str, host: str | None = None) -> str:
    """Run a vision OCR model on one base64 image. ``model_id`` must be vision-capable."""
    try:
        resp = _client(host).chat(
            model=model_id,
            messages=[{"role": "user", "content": prompt, "images": [image_b64]}],
            options={"temperature": 0.0, "num_ctx": OCR_NUM_CTX},
        )
        return resp["message"]["content"]
    except Exception as exc:
        raise RuntimeError(f"Ollama OCR failed ({model_id}): {exc}") from exc


def rewrite(model_id: str, prompt: str, host: str | None = None) -> str:
    """Reformat text into Markdown via a text model."""
    try:
        resp = _client(host).chat(
            model=model_id,
            messages=[{"role": "user", "content": prompt}],
            options={"temperature": 0.0, "num_ctx": REWRITE_NUM_CTX},
        )
        return resp["message"]["content"]
    except Exception as exc:
        raise RuntimeError(f"Ollama rewrite failed ({model_id}): {exc}") from exc


def unload(model_id: str, host: str | None = None) -> None:
    """Evict a model from VRAM (keep_alive=0) so the next model gets the full GPU.

    Best-effort: a failure here only costs memory, never correctness.
    """
    try:
        _client(host).generate(model=model_id, prompt="", keep_alive=0)
    except Exception:
        pass


def unload_all(host: str | None = None) -> list[str]:
    """Evict every currently loaded Ollama model from VRAM. Returns their names.

    Best-effort: a failure here only costs memory, never correctness.
    """
    client = _client(host)
    try:
        loaded = [m.model for m in client.ps().models]
    except Exception:
        return []
    for model_id in loaded:
        try:
            client.generate(model=model_id, prompt="", keep_alive=0)
        except Exception:
            pass
    return loaded
