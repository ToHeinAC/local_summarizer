# Models

`src/models.py` registers the selectable Ollama LLMs and checks which are
installed on the local server.

| id | tag | label | speed | quality |
|---|---|---|---|---|
| `fast` | `gemma4:e2b` | Schnell | 3 | 1 |
| `standard` *(default)* | `gemma4:e4b` | Standard | 2 | 2 |
| `smarter` | `qwen3:14b` | Klüger | 1 | 3 |
| `accurate` | `gpt-oss:20b` | Genau | 1 | 3 |

`speed`/`quality` are 1-3 metrics rendered as stars in the UI. Tags match the
PRD and the user's `ollama list`. `label` and `note` are German — they are shown
verbatim in the sidebar.

## API
- `list_models()` / `get_model(id)` (raises `KeyError` if unknown)
- `installed_tags(host) -> set[str]` — queries `GET {host}/api/tags` via stdlib
  `urllib`; returns an empty set if the server is unreachable (no crash).
- `annotate_availability(host) -> list[dict]` — each model plus an `installed`
  bool. The UI warns and disables **Zusammenfassen** for uninstalled models,
  suggesting `ollama pull <tag>`.
