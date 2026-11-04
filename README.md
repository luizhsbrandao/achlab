# achlab

Analysis of Competing Hypotheses with auditable provenance.

**Status:** M1 — the CLI works end to end on the synthetic case. Not published yet (M2 adds
MCP, PyPI and the public repo). The durable spec lives in the project's private knowledge vault.

The design rule is the same as `academia-tooling`: **verify, don't generate**. Every evidence
item carries a citable source; every assessment carries a rationale; a report with incomplete
provenance is refused (exit 3) unless explicitly stamped `NÃO CITÁVEL`.

## Install (development)

```bash
python3 -m venv .venv
.venv/bin/pip install -e ".[dev]"
```

## Try it

```bash
.venv/bin/ach demo
```

The demo uses a synthetic case (3 hypotheses, 9 evidence items) and prints the consistency
matrix, the ranking by least inconsistency, margin, leave-one-out robustness and the confidence
band.

## Workflow

```bash
ach init "Who disclosed the memo?" --dir case-001
ach hyp add "H1: an insider did it" --dir case-001
ach hyp add "H2: an external contractor did it" --dir case-001
ach ev add --title "Badge log" --source "Synthetic badge log" \
  --reliability A --credibility 2 --relevance alta \
  --excerpt "22:14 access, the only one after 20:00" \
  --locator "fixture://badge/2026-01-01" --dir case-001
ach assess E1 H1 --consistency ++ --rationale "..." --dir case-001
ach assess E1 H2 --consistency -- --rationale "..." --dir case-001
ach ev accept E1 --dir case-001
ach score --dir case-001
ach report --dir case-001 --md case-001/report.md
ach validate --dir case-001
```

Exit codes: `0` ok, `1` operational error, `2` integrity/schema violation, `3` report refused
for incomplete provenance.

## Test

```bash
.venv/bin/python -m pytest -q
```

44 tests, including the tie case, non-diagnostic evidence, the decisive-evidence search and the
absolute-margin floor found in the M0 spike.

## License

MIT.
