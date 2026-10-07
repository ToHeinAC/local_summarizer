# Models

`src/models.py` registers the selectable Ollama LLMs and checks which are
installed on the local server.

| id | tag | label | speed | quality |
|---|---|---|---|---|
| `fast` | `LiquidAI/lfm2.5-1.2b-instruct:latest` | Schnell / Fast | 3 | 1 |
| `standard` *(default)* | `gemma4:e4b` | Standard | 2 | 2 |
| `smarter` | `qwen3:14b` | Klüger / Smarter | 1 | 3 |
| `accurate` | `gpt-oss:20b` | Genau / Accurate | 1 | 3 |
| `qwen38` | `qwen3.8-27b:latest` | Qwen3.8 (27B) | 1 | 3 |
| `hybrid` | `qwen3.8-27b:latest` + `map_tag` `gemma4:e4b` | Hybrid | 2 | 3 |

`qwen38`'s tag is not an official Ollama registry model: it is a local
`ollama create` of the GGUF from the sibling
[`local-llm-testing`](https://github.com/ToHeinAC/local-llm-testing) repo
(`models/Qwen3.8-27B-UD-Q4_K_XL.gguf`, ~17.5 GB):

```bash
printf 'FROM /path/to/local-llm-testing/models/Qwen3.8-27B-UD-Q4_K_XL.gguf\n' > Modelfile
ollama create qwen3.8-27b -f Modelfile
```

`ollama create` with no `:tag` on the name defaults to `:latest` — that is why
the registry tag is `qwen3.8-27b:latest` and not `qwen3.8-27b`; `ollama list`
would otherwise show the model as present while `annotate_availability`'s exact
string match against `/api/tags` still says "not installed".

Until that has been run once on the box, `annotate_availability` reports it as
`installed: False` like any other un-pulled model — the UI warns and disables
**Zusammenfassen** for it, same as the others. At 17.5 GB it is the largest
model in the registry and benefits the most from GPU pinning (see
[gpu.md](gpu.md)): unpinned it is split across both cards (29 tok/s measured),
pinned to one it reaches ~44 tok/s.

`speed`/`quality` are 1-3 metrics rendered as stars in the UI. Tags match the
PRD and the user's `ollama list`. `label` and `note` are `{"de": ..., "en": ...}`
dicts read with `i18n.pick`, so the sidebar follows the GUI language.

`hybrid` exists because running the 27B over every chunk is very slow. Its
`map_tag` (`gemma4:e4b`) handles the map and reduce passes; `tag` (Qwen3.8) runs
only the finalize node, so it sees one short prompt. `agent._finalize` evicts the
map model first (`ollama_client.unload`) so the 27B gets the GPU. Single-chunk
documents use Qwen3.8 only. Live check: 34k chars / 6 chunks in ~74 s.

## API
- `list_models()` / `get_model(id)` (raises `KeyError` if unknown)
- `installed_tags(host) -> set[str]` — queries `GET {host}/api/tags` via stdlib
  `urllib`; returns an empty set if the server is unreachable (no crash).
- `model_tags(model)` — all tags a model needs (`tag` + optional `map_tag`).
- `annotate_availability(host) -> list[dict]` — each model plus an `installed`
  bool (all needed tags present) and a `missing` tag list. The UI warns and disables **Zusammenfassen** / **Summarize** for
  uninstalled models,
  suggesting `ollama pull <tag>`.
