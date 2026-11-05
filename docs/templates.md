# Templates

`src/templates.py` holds a registry of summary templates. Each entry's
`structure` string is injected into `FINALIZE_PROMPT` to steer format and
information density.

| id | label | Length | Shape |
|---|---|---|---|
| `executive` | Executive Summary (½ Seite) | 250-300 words | Three prose paragraphs: document + objective, decisive results, conclusions/next steps. No headings |
| `bullets` *(default)* | Stichpunkte (1 Seite) | 450-550 words | `## Objective`, `## Methodology`, `## Results` — bullets only |
| `detailed` | Ausführlich mit Referenzen (2 Seiten) | 1000-1200 words | Objective, Methodology, Results with one `### ` per major topic, Conclusions, `## References` list; inline verbatim citations (§/clause, figure/table, quantities, `[BS 04]`-style keys) |
| `action_items` | Maßnahmen (1 Seite) | 450-550 words | One-line Objective and Methodology, then `## Key Findings`, `## Conclusions`, `## Measures` (verb first, owner/deadline/target value where stated) |

Page targets are passed to the LLM as **word counts** (one A4 page of prose ≈
500 words); word counts steer a small model far better than page counts (measured within ~15 % of the target, bullets tending short). Heading
names are English in `structure`; `FINALIZE_PROMPT` has the model translate them
into the summary language.

These four replaced six earlier templates (`standard`, a plain `detailed`
without anchors, `detailed_refs`, flat `bullets`, …) on user request. Every
report type now leads with objective and methodology because that is what the
user reads first; only `detailed` lists references, so only it needs the
anchors that `MAP_PROMPT`/`REDUCE_PROMPT` carry through verbatim (see
[agent.md](agent.md)).

## API
- `list_templates() -> list[dict]`
- `get_template(id) -> dict` (raises `KeyError` if unknown)
- `DEFAULT_TEMPLATE_ID = "bullets"`

`label` and `description` are `{"de": ..., "en": ...}` dicts (UI-facing, read
with `i18n.pick`); `structure` stays English because it is prompt text.

## Adding a template
Append a dict with `id`, `label`, `description`, `structure` — `label` and
`description` need both language keys. The UI and prompt
pick it up automatically; keep `structure` explicit about headings/lists so the
model follows it and the export renderer formats it (see [export.md](export.md)).
