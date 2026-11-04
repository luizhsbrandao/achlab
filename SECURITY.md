# Security policy

`achlab` is for **unclassified, public-source analysis only**. Do not use it with classified
information, personal data, or material you are not authorized to store. The tool has no access
control, no encryption and no audit server: it is a local file format plus a CLI.

## Reporting a vulnerability

Send a private report to **intellecta.contact@proton.me** with the subject `[achlab security]`.
Do not open a public issue for a vulnerability. Include the version, a minimal reproduction and
the impact. You should receive an acknowledgement within seven days.

## Scope

- The CLI reads and writes a project directory chosen by the user.
- The MCP server is read-only and restricted to `--root`; it refuses paths outside that root.
- The core has no network calls. The optional MCP transport uses stdio.
- Dependencies: none at runtime; `mcp` only when the `[mcp]` extra is installed.

## Data handling

- Fixtures and tests are synthetic; do not contribute real correspondence, names or documents.
- Reports contain citations and excerpts; review them before sharing.
- Never commit credentials, tokens, `.env` files or private keys. Use a local `.env` outside the
  repository.
- If you find a secret in the repository or its history, report it privately; do not open a PR
  that reproduces it.

## Supported versions

Security fixes are applied to the latest `0.1.x` release. Older versions are not supported.
