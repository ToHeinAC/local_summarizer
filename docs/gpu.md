# GPU placement

> Modules: [`src/gpu_placement.py`](../src/gpu_placement.py) (policy),
> [`src/ollama_server.py`](../src/ollama_server.py) (the pinned Ollama daemon).
> Ported from
> [KB_BS_local-wiki-he](https://github.com/ToHeinAC/KB_BS_local-wiki-he)
> (Apache-2.0), which runs on the same box.

## The policy

**Keep the model on one GPU unless it cannot fit.**

Splitting a model's layers across cards does not make single-stream decoding
faster. The GPUs run *sequentially* — each idles while the other works — and
every token pays a cross-device hop. A split buys capacity, not speed, so it is
worth taking only when one card cannot hold the model.

Measured on this box (2× RTX 4090) with the sibling
[`local-llm-testing`](https://github.com/ToHeinAC/local-llm-testing) bench
harness:

| Setup | tok/s |
|---|---|
| Ollama, shared system daemon (split, `NUM_PARALLEL=4`, ctx 131072) | 149 |
| Ollama, pinned daemon (`NUM_PARALLEL=1`, ctx 8192) | **164** |
| llama.cpp, split across both cards, ctx 8192 | 94 |
| llama.cpp, pinned to one card, ctx 8192 | **170** |

The Ollama pair is not a clean placement A/B — placement, parallelism *and*
context all differ, because the shared daemon's settings are not ours to
change. Treat 149 → 164 as "the daemon we control beats the one we don't", not
as a pure placement delta. The llama.cpp figures (not used by this app, which
only talks to Ollama) show the placement effect in isolation.

## Two traps

Both cost a debugging round-trip; neither is re-derivable from the symptom.

1. **`CUDA_VISIBLE_DEVICES` alone silently fails for Ollama.** Ollama offers
   every card through CUDA *and* Vulkan. Hiding a card from CUDA makes it
   reappear as a Vulkan device and the model loads there anyway — asking for
   GPU 1 lands you on GPU 0, with no error. **`OLLAMA_VULKAN=0`** is what makes
   the CUDA filter authoritative.
2. **CUDA orders devices fastest-first, not by PCI bus.** Without
   **`CUDA_DEVICE_ORDER=PCI_BUS_ID`**, index *N* need not be nvidia-smi's GPU
   *N*. `gpu_placement.cuda_env()` always emits both variables together.

## A daemon of our own

The system daemon on `:11434` runs as `User=ollama` with
`OLLAMA_NUM_PARALLEL=4` (`/etc/systemd/system/ollama.service.d/`) and no device
pin. Its environment needs root to change, and restarting it would drop
whatever the box's other apps have loaded. So this app does not touch it.

Instead `ollama_server` starts a **second `ollama serve`** on a spare port
(`OLLAMA_PIN_PORT`, default `11435`) against the **same model store** — no
copy, no re-pull; the store is world-readable — pinned to one card, and every
caller in the app reaches Ollama through `ollama_server.host()`:

```
app._run() / _model_selector() / _sidebar()
   └─ ollama_server.host() ─┬─ configured OLLAMA_HOST is remote?     → use it unchanged
                            ├─ OLLAMA_PIN_GPU=off?                   → use it unchanged
                            ├─ OCR + REWRITE models too big for one? → use it unchanged
                            ├─ :11435 already serving?                → adopt it
                            └─ spawn `ollama serve` on :11435 ──┬─ up   → use it
                                                                 └─ down → use :11434
```

Every branch that is not a pin returns the configured `OLLAMA_HOST`
**unchanged** and the app behaves exactly as it did before. `ollama_server.status()`
reports which branch was taken; the sidebar's **Advanced options** expander
shows it (`Ollama · GPU 1 (pinned)`, or `Ollama · shared daemon (…reason…)`).

**What the child gets:** `CUDA_VISIBLE_DEVICES` + `CUDA_DEVICE_ORDER` from
`cuda_env()`, `OLLAMA_VULKAN=0`, `OLLAMA_NUM_PARALLEL=1`,
`OLLAMA_HOST=127.0.0.1:<port>`, and `OLLAMA_MODELS` from `find_models_dir()`.

**Finding the model store** is deliberately "the candidate with the most
manifests", not "the first that exists": `~/.ollama/models` can exist empty
while every model lives in the system daemon's store
(`/usr/share/ollama/.ollama/models` on this box), so picking by existence would
start a daemon that can see no models at all.

**The size estimate** (`required_gib`) sums `OCR_MODEL` and `REWRITE_MODEL` —
the two roles `src/md_convert.py` always uses automatically and that are fixed
by `.env` ahead of time. The user-selected *summarization* model
(`src/models.py`) is **not** included: it is chosen per request in the UI, so
it cannot be sized before the daemon starts. This under-estimates on purpose —
a model never pulled contributes 0, and an unreachable daemon leaves only the
compute overhead — because the safer failure mode here is attempting a pin,
not refusing one.

**Lifecycle.** Started lazily on the first `host()` call, stopped via `atexit`,
so Streamlit's SIGTERM shutdown reaps it. A daemon already listening on the
pinned port is **adopted**, not duplicated, so a hard kill leaves at most one
stray daemon and the next app start reuses it. `stop()` never touches an
adopted daemon — only one this process started.

The one sharp edge: **run a single instance of this app per pinned port.** With
two up at once the second adopts the first's daemon, and if the owner exits
first the adopter is left pointing at a dead host (the resolution is cached, so
it will not re-resolve on its own). Give a second instance its own
`OLLAMA_PIN_PORT`, or set `OLLAMA_PIN_GPU=off` on it.

## Verifying

```bash
# what the app resolved, without starting the UI
uv run python -c "from src import ollama_server; import json; print(json.dumps(ollama_server.status(), indent=2))"

# where the weights actually landed
nvidia-smi --query-gpu=index,memory.used,utilization.gpu --format=csv
```

A correct pin shows the whole model on one card and the other card flat at its
baseline — that is the check that catches the Vulkan trap, which a status line
alone cannot.

## Turning it off

`OLLAMA_PIN_GPU=off` restores the previous behaviour exactly: the shared
`:11434` daemon, unpinned. `"0"` is **not** an off-switch — it names GPU 0.
