# achlab

*Analysis of Competing Hypotheses* with auditable provenance. Full documentation in Portuguese:
[README.pt-BR.md](README.pt-BR.md).

**Status:** M2 — release candidate. CLI, read-only MCP server and 51 tests.

The design rule is **verify, don't generate**: every evidence item carries a citable source,
every assessment carries a rationale, and a report with incomplete provenance is refused
(exit 3) unless it is explicitly stamped `NÃO CITÁVEL`.

## Install (development)

```bash
python3 -m venv .venv
.venv/bin/pip install -e ".[dev]"
.venv/bin/ach demo
```

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

Exit codes: `0` ok · `1` operational error · `2` integrity/schema violation · `3` report refused
for incomplete provenance.

## MCP (read-only)

```bash
pip install "achlab[mcp]"
ach-mcp --root ~/analyses
```

Tools: `ach_list_projects`, `ach_get_project`, `ach_score`, `ach_report`. None of them writes;
the analysis is written through the CLI, with a human decision.

## Documentation

- [Method](docs/metodo.md)
- [Scoring](docs/pontuacao.md)
- [Provenance and exit codes](docs/proveniencia.md)

## Test

```bash
.venv/bin/python -m pytest
```

51 tests: matrix, tie, non-diagnostic evidence, decisive-evidence search, absolute-margin floor,
integrity validation, CLI and MCP.

## License

MIT. Contributions: [CONTRIBUTING.md](CONTRIBUTING.md). Security: [SECURITY.md](SECURITY.md).
