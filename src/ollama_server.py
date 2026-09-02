"""An Ollama daemon of our own, pinned to one GPU. Plain python, no LangChain.

The shared system daemon on :11434 runs as `User=ollama` with
`OLLAMA_NUM_PARALLEL=4` and no device pin, so its models land split across both
cards. Its environment needs root to change, and restarting it would drop
whatever the box's other apps have loaded, so this module does not touch it.
Instead it starts a **second** `ollama serve` on a spare port against the *same
model store* — no copy, no re-pull, the store is world-readable — pinned to one
card via `gpu_placement`, and the app reaches Ollama through `host()` alone.

FAIL-OPEN. No `ollama` binary, no GPU, a model too big for one card, a port
that will not come up — every one of them returns the configured `OLLAMA_HOST`
unchanged, and the app behaves exactly as it does today. `status()` says which
branch was taken.

Lifecycle: started lazily on the first `host()` call and stopped via `atexit`,
so Streamlit's SIGTERM shutdown reaps it. A daemon already listening on the
pinned port is **adopted** rather than duplicated, so a hard kill (SIGKILL, a
crash) leaves at most one stray daemon and the next app start reuses it.

Ported from
`KB_BS_local-wiki-he <https://github.com/ToHeinAC/KB_BS_local-wiki-he>`_
(Apache-2.0), which runs on the same box. One difference: this app's
summarization model is chosen per request in the UI (``src/models.py``), not
fixed by an env var, so it cannot be sized in advance — `required_gib` only
sums the two roles that run automatically and are fixed ahead of time,
`OCR_MODEL` and `REWRITE_MODEL` (see ``src/md_convert.py``). Keep the defaults
below in step with ``src/config.py``; a drift only skews the size estimate,
never correctness.
"""

from __future__ import annotations

import atexit
import json
import os
import shutil
import subprocess
import threading
import time
import urllib.error
import urllib.request
from pathlib import Path
from urllib.parse import urlsplit

from dotenv import load_dotenv

from src import gpu_placement

load_dotenv()

DEFAULT_HOST = "http://localhost:11434"
# Spare port for the pinned daemon. Deliberately not 11434 — the shared daemon
# and the box's other apps keep that one.
DEFAULT_PORT = 11435
_STARTUP_TIMEOUT_S = 40.0

# The two model roles this app always uses automatically (src/md_convert.py),
# and the defaults each falls back to if unset. Read from the environment
# rather than from config.py so this module stays free of an import cycle.
_MODEL_ENV = {
    "OCR_MODEL": "deepseek-ocr:3b",
    "REWRITE_MODEL": "LiquidAI/lfm2.5-1.2b-instruct:latest",
}

_lock = threading.Lock()
_state: dict | None = None
_proc: subprocess.Popen | None = None


# ---------------------------------------------------------------------------
# configuration


def configured_host() -> str:
    """`OLLAMA_HOST` as the ollama SDK would read it, normalised to a URL."""
    raw = (os.getenv("OLLAMA_HOST") or DEFAULT_HOST).strip() or DEFAULT_HOST
    return raw if "://" in raw else f"http://{raw}"


def _is_local(url: str) -> bool:
    return (urlsplit(url).hostname or "") in ("localhost", "127.0.0.1", "::1", "0.0.0.0")


def _pinned_port() -> int:
    try:
        return int(os.getenv("OLLAMA_PIN_PORT", str(DEFAULT_PORT)))
    except ValueError:
        return DEFAULT_PORT


# ---------------------------------------------------------------------------
# the model store and its sizes


def _store_candidates() -> tuple[str | None, ...]:
    """Where an Ollama model store can live, most-specific first."""
    return (os.getenv("OLLAMA_MODELS"), os.path.expanduser("~/.ollama/models"),
            "/usr/share/ollama/.ollama/models", "/var/lib/ollama/.ollama/models")


def find_models_dir() -> str | None:
    """The store holding the most manifests, or None if no candidate has any.

    Not "the first that exists": `~/.ollama/models` can exist empty while every
    model actually lives in the system daemon's store, so picking by existence
    would start a daemon that can see no models at all.
    """
    best, best_count = None, 0
    for candidate in _store_candidates():
        if not candidate:
            continue
        manifests = Path(candidate) / "manifests"
        if not manifests.is_dir():
            continue
        try:
            count = sum(1 for p in manifests.rglob("*") if p.is_file())
        except OSError:
            continue
        if count > best_count:
            best, best_count = str(Path(candidate)), count
    return best


def configured_models() -> set[str]:
    """The model names this app always reaches for automatically."""
    names = {(os.getenv(key) or default).strip() for key, default in _MODEL_ENV.items()}
    names.discard("")
    return names


def _get_json(url: str, timeout: float = 3.0) -> dict | None:
    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, OSError, ValueError, json.JSONDecodeError):
        return None


def required_gib(source_host: str) -> float:
    """VRAM the OCR and rewrite models need if resident together.

    Both run during PDF conversion (``src/md_convert.py``) and can be loaded at
    once. The user-selected summarization model is not included — it varies per
    request and cannot be sized ahead of the daemon starting. Sizes come from
    the already-running daemon's /api/tags; a model never pulled contributes 0,
    and an unreachable daemon yields just the overhead — both under-estimate,
    which is the right bias: if no daemon answers, ours is the app's only LLM.
    """
    tags = _get_json(f"{source_host}/api/tags") or {}
    sizes: dict[str, float] = {}
    for model in tags.get("models", []) or []:
        name, size = model.get("name"), model.get("size")
        if not isinstance(name, str) or not isinstance(size, (int, float)):
            continue
        sizes[name] = size / gpu_placement.GIB
        sizes.setdefault(name.removesuffix(":latest"), size / gpu_placement.GIB)
    return sum(sizes.get(n, 0.0) for n in configured_models()) + gpu_placement.COMPUTE_OVERHEAD_GIB


# ---------------------------------------------------------------------------
# daemon lifecycle


def _serving(base: str) -> bool:
    return _get_json(f"{base}/api/tags", timeout=1.0) is not None


def _spawn(port: int, gpu_index: int) -> subprocess.Popen | None:
    binary = shutil.which("ollama")
    if not binary:
        return None
    env = {**os.environ, **gpu_placement.cuda_env(gpu_index),
           "OLLAMA_HOST": f"127.0.0.1:{port}",
           # Without this the card hidden from CUDA reappears as a Vulkan device
           # and the model loads there anyway. See gpu_placement's module docstring.
           "OLLAMA_VULKAN": "0",
           "OLLAMA_NUM_PARALLEL": "1"}
    models_dir = find_models_dir()
    if models_dir:
        env["OLLAMA_MODELS"] = models_dir
    try:
        # start_new_session: the daemon's lifetime is decided by stop() alone, so
        # a Ctrl-C aimed at the app's process group cannot kill it mid-request.
        return subprocess.Popen([binary, "serve"], env=env, stdout=subprocess.DEVNULL,
                                stderr=subprocess.DEVNULL, start_new_session=True)
    except OSError:
        return None


def _wait_until_serving(proc: subprocess.Popen, base: str, timeout_s: float) -> bool:
    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        if proc.poll() is not None:
            return False
        if _serving(base):
            return True
        time.sleep(0.25)
    return False


def stop() -> None:
    """Terminate the daemon if we started it. Adopted daemons are left running."""
    global _proc
    proc, _proc = _proc, None
    if proc is None or proc.poll() is not None:
        return
    proc.terminate()
    try:
        proc.wait(timeout=10)
    except subprocess.TimeoutExpired:
        proc.kill()


atexit.register(stop)


# ---------------------------------------------------------------------------
# resolution


def _resolve() -> dict:
    global _proc
    fallback = configured_host()
    mode = os.getenv("OLLAMA_PIN_GPU", "auto")

    def unpinned(reason: str) -> dict:
        return {"host": fallback, "pinned": False, "gpu": None,
                "managed": False, "reason": reason}

    if not _is_local(fallback):
        return unpinned(f"OLLAMA_HOST is remote ({fallback}) — left untouched")

    placement = gpu_placement.plan(required_gib(fallback), mode)
    if not placement.is_pinned:
        return unpinned(placement.reason)

    port = _pinned_port()
    base = f"http://127.0.0.1:{port}"
    if _serving(base):
        return {"host": base, "pinned": True, "gpu": placement.index, "managed": False,
                "reason": f"reusing the pinned daemon already on port {port}"}

    proc = _spawn(port, placement.index)
    if proc is None:
        return unpinned("no `ollama` binary on PATH — cannot start a pinned daemon")
    if not _wait_until_serving(proc, base, _STARTUP_TIMEOUT_S):
        proc.kill()
        return unpinned(f"pinned daemon did not come up on port {port}")
    _proc = proc
    return {"host": base, "pinned": True, "gpu": placement.index, "managed": True,
            "reason": placement.reason}


def host() -> str:
    """The Ollama base URL every caller in this app must use."""
    return status()["host"]


def status() -> dict:
    """Resolved placement: host, pinned, gpu, managed, reason. Cached per process."""
    global _state
    with _lock:
        if _state is None:
            _state = _resolve()
        return dict(_state)


def reset() -> None:
    """Drop the cached resolution and stop a daemon we own (tests, maintenance)."""
    global _state
    with _lock:
        _state = None
    stop()
