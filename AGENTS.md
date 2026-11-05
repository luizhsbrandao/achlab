# AGENTS.md — achlab

Regras para qualquer agente (Claude Code, Antigravity, OpenCode) que trabalhe neste repositório.
Vale junto com `~/.agents/STATION-RULES.md`; onde as duas falarem, vale a mais restritiva.

## O que é

`achlab` — *Analysis of Competing Hypotheses* com proveniência auditável. CLI (`ach`), servidor MCP
read-only e 51 testes. Biblioteca, sem dependências de runtime (`dependencies = []`).

A regra de desenho é **verificar, não gerar**: cada item de evidência carrega fonte citável, cada
avaliação carrega justificativa, e relatório com proveniência incompleta é **recusado com exit 3**
até ser carimbado `NÃO CITÁVEL`. Não afrouxe essa recusa para fazer teste passar — é o produto.

## Comandos

```bash
.venv/bin/python -m pytest -q          # suíte completa (51 testes) — é a verificação canônica
.venv/bin/pip install -e ".[dev]"      # instala se .venv não existir
.venv/bin/ach demo                     # demo do CLI
```

`ruff` não está configurado neste repo: não invente lint que não existe. Não rode `npm`, `make` ou
instalador de terceiro.

## Regras

- **Não edite** `dist/`, `build/` nem `spikes/` — são saída de build e experimentos congelados.
- **Não mude a superfície pública** (`ach` CLI, nomes de campo do modelo, formato de relatório) sem
  autorização explícita: há consumidor fora do repo.
- Teste novo só entra se provar comportamento — não teste que espelha a implementação.
- Diff pequeno, um assunto por commit. Mensagem em português, imperativa, com o porquê.
- **Nunca** `git push`, `git add -A`, `git reset --hard`, `git clean`. A árvore fica pronta; commit e
  push são do operador.
- **Nunca** `--dangerously-skip-permissions`, nunca `--auto`.
- Segredo não se lê (`.env`, `*.pem`, `*.key`, `.ssh`, `.gnupg`) e não se escreve em código.
  O `pre-commit` deste repo roda gitleaks com regras explícitas (`.gitleaks.toml`) e **falha fechado**.

## Verificação

Quem roda teste é o operador ou o wrapper — não você. Se você tem shell, use **apenas**
`.venv/bin/python -m pytest`; qualquer outro comando é motivo de recusa. Relate o que verificou de
fato, com o comando e a saída; "deve funcionar" não é resultado.
