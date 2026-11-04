# Provenance and exit codes

The identity of the tool is the provenance gate: **no source, no verdict**.

## Evidence lifecycle

| Status | Meaning | Used in scoring? |
|---|---|---|
| `draft` | added but not yet accepted | no |
| `aceita` | citation + excerpt + locator present | yes |
| `rejeitada` | explicitly rejected, with a reason | no |

`ach ev add` always creates a `draft`. `ach ev accept <id>` validates the gate and only then
marks it `aceita`. An accepted item must have:

- `source.citation` — author/title/date or equivalent;
- `excerpt` — the short passage that supports the assessment (≤ 500 characters is the intended
  size; the model does not truncate it silently);
- a locator — `source.url`, `source.archive_url` or `source.locator` (page, file, archive id).

Assessments are only stored with a non-empty rationale. A hypothesis can only be rejected with a
reason; rejection is not deletion.

## Reports and exit codes

| Code | When |
|---|---|
| `0` | success |
| `1` | operational error: missing project, unknown id, duplicate id |
| `2` | integrity/schema violation: missing citation, missing rationale, invalid scale, unknown reference |
| `3` | `ach report` refused because provenance < 1.0 |

`ach validate` returns `2` and prints every violation. `ach report` returns `2` for integrity
errors and `3` for incomplete provenance. `ach report --allow-incomplete` produces the report
with a first-line watermark:

```
> **ANÁLISE INCOMPLETA — NÃO CITÁVEL**
```

The watermark is deliberately ugly. A report with drafts is not a citable product.

## Provenance ratio

```
provenance = accepted items with citation + excerpt + locator / all items
```

Drafts and rejected items count in the denominator. The confidence band uses the ratio:
`< 30%` forces `INDETERMINADA`; `< 50%` blocks `MODERADA`; `< 80%` blocks `ALTA`.

## Audit trail

Every mutation appends a line to `events.jsonl`:

```json
{"ts": "2026-11-04T16:00:00+00:00", "action": "assess", "object": "E1/H1", "detail": "++"}
```

The project file itself is deterministic JSON and can be versioned in git. The event log is
append-only; it records who changed what, not a hash chain. For evidentiary use, commit the
project directory to git and tag the analysis version.

## MCP

The MCP server is read-only: `ach_list_projects`, `ach_get_project`, `ach_score`, `ach_report`.
It only reads under `--root`, refuses paths outside it, and rejects a `project.json` symlink
whose target escapes the root. There is no MCP tool to accept evidence or record an assessment;
those are human decisions made through the CLI.
