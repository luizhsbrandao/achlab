# Contributing

Thanks for considering a contribution. The project is small and deliberately conservative.

## Setup

```bash
python3 -m venv .venv
.venv/bin/pip install -e ".[dev]"
.venv/bin/python -m pytest
```

The test suite runs on Python 3.11, 3.12 and 3.13 in CI. The core has no runtime dependencies;
please keep it that way. The MCP server depends on `mcp` only through the optional extra.

## Rules

- **Never commit real data.** Fixtures are synthetic, including names, citations and locators.
  Do not contribute personal data, classified material or copyrighted documents.
- **Never commit secrets.** No tokens, keys, `.env` files or credentials in tests, docs or
  fixtures. If you find one, report it privately (see `SECURITY.md`).
- **Every scoring change needs a test and a docs update.** The formulas in `docs/pontuacao.md`
  are the contract; a change without both is incomplete.
- **Every new check needs a failing fixture.** A check that cannot fail is not a check.
- **Keep the core deterministic.** No LLM calls, no network, no timestamps in generated reports.
  A report must be byte-identical for the same project.
- **English entry, Portuguese detail.** The public README is English; `README.pt-BR.md` carries
  the full Portuguese explanation. Keep both links working.

## Commit style

Short imperative subject, then the why in the body when it is not obvious. Sign your commits if
you can; the maintainer's are signed with an SSH key.

## Pull requests

1. Open an issue for a behavior change before writing a large patch.
2. Add tests and run the full suite.
3. Update the docs that the change invalidates.
4. Describe what was measured, not what "should" work.

## License

By contributing you agree that your contribution is licensed under the MIT license.
