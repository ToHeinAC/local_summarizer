# Templates

`src/templates.py` holds a registry of summary templates. Each entry's
`structure` string is injected into `FINALIZE_PROMPT` to steer format and
information density.

| id | label | Shape |
|---|---|---|
| `executive` | Management (knapp) / Executive (terse) | One 3-5 sentence paragraph, no headings |
| `standard` *(default)* | Standard | `## Overview` + `## Key Points` bullets |
| `detailed` | Ausführlich / Detailed | Overview + per-topic `### ` subsections + conclusion |
| `bullets` | Stichpunkte / Bullet key-points | Flat 6-20 bullet takeaways |
| `action_items` | Maßnahmen / Action items | `## Decisions` + `## Action Items` lists |

## API
- `list_templates() -> list[dict]`
- `get_template(id) -> dict` (raises `KeyError` if unknown)
- `DEFAULT_TEMPLATE_ID = "standard"`

`label` and `description` are `{"de": ..., "en": ...}` dicts (UI-facing, read
with `i18n.pick`); `structure` stays English because it is prompt text.

## Adding a template
Append a dict with `id`, `label`, `description`, `structure` — `label` and
`description` need both language keys. The UI and prompt
pick it up automatically; keep `structure` explicit about headings/lists so the
model follows it and the export renderer formats it (see [export.md](export.md)).
