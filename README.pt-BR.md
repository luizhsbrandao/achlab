# achlab — ACH com proveniência auditável

*Analysis of Competing Hypotheses* (ACH) é uma técnica estruturada de análise: em vez de
procurar evidência que confirme a hipótese preferida, o analista compara hipóteses rivais e
procura a que tem **menos evidência contra**. O `achlab` implementa essa lógica de forma
determinística e auditável, com uma regra de projeto: **verificar, não gerar**.

- Toda evidência tem fonte citável (citação + trecho + localizador).
- Toda avaliação tem justificativa.
- O relatório mostra a matriz, o cálculo, a margem, a robustez e as lacunas.
- Sem LLM no núcleo; sem linguagem probabilística.
- Nenhum dado real ou classificado nas fixtures.

## Instalar

```bash
python3 -m venv .venv
.venv/bin/pip install -e ".[dev]"
```

Requer Python ≥ 3.11. Dependência de execução: nenhuma (stdlib). O servidor MCP é opcional:
`pip install -e ".[mcp]"`.

## Tentar

```bash
.venv/bin/ach demo
```

O caso é sintético: três hipóteses (insider, prestador, falha de configuração) e nove
evidências. A saída mostra a matriz, o ranking, a margem, a robustez e a faixa.

## Fluxo completo

```bash
ach init "Quem divulgou o rascunho?" --dir caso-001
ach hyp add "H1: alguém do financeiro" --definition "acesso presencial ou remoto" --dir caso-001
ach hyp add "H2: um prestador externo" --dir caso-001

ach ev add --title "Log de crachá" --source "Log sintético de crachá" \
  --reliability A --credibility 2 --relevance alta \
  --excerpt "Acesso às 22:14; único após as 20:00" \
  --locator "fixture://log-cracha/2026-01-01" --dir caso-001

ach assess E1 H1 --consistency ++ --rationale "Acesso presencial compatível." --dir caso-001
ach assess E1 H2 --consistency -- --rationale "Prestador não tinha crachá." --dir caso-001

# Ainda é draft: o relatório recusa (exit 3)
ach report --dir caso-001

ach ev accept E1 --dir caso-001
ach validate --dir caso-001
ach score --dir caso-001
ach report --dir caso-001 --md caso-001/report.md
```

`--consistency` aceita `++`, `+`, `0`, `-`, `--` e `na`. O valor `--` funciona como argumento
separado (a CLI normaliza antes do parser).

## O que o relatório contém

1. Matriz de consistência: evidência × hipótese, com peso (`w`) e diagnosticidade (`D`).
2. Ranking por menor inconsistência (`I`), com suporte (`S`) apenas informativo.
3. Margem absoluta e relativa; empate técnico vira `INDETERMINADO`.
4. Robustez *leave-one-out* e a lista de evidências decisivas.
5. Proveniência, evidências diagnósticas e faixa de confiança.
6. Fontes completas e evidências não usadas (drafts/rejeitadas).
7. Premissas (Key Assumptions Check), quando registradas.

## Códigos de saída

| Código | Significado |
|---|---|
| `0` | sucesso |
| `1` | erro operacional (projeto ausente, id inexistente) |
| `2` | violação de integridade ou schema |
| `3` | relatório recusado: proveniência incompleta |

O `--allow-incomplete` gera o relatório com o carimbo **ANÁLISE INCOMPLETA — NÃO CITÁVEL**.

## MCP (somente leitura)

```bash
pip install "achlab[mcp]"
ach-mcp --root ~/analises
```

Ferramentas: `ach_list_projects`, `ach_get_project`, `ach_score`, `ach_report`. O servidor lê
apenas sob `--root`; nenhuma ferramenta escreve. Para integrar ao Hermes, declare o servidor em
`mcp_servers` no `config.yaml`:

```yaml
mcp_servers:
  achlab:
    command: ach-mcp
    args: ["--root", "/home/<usuario>/analises"]
```

## Método

A especificação do método está em [docs/metodo.md](docs/metodo.md), a pontuação com exemplo
calculado à mão em [docs/pontuacao.md](docs/pontuacao.md) e o portão de proveniência em
[docs/proveniencia.md](docs/proveniencia.md).

Resumo: a hipótese com **menor inconsistência ponderada** é a que sobrevive; evidência
consistente com todas as hipóteses não discrimina e não ranqueia; a faixa de confiança mede a
robustez da análise, não a probabilidade da hipótese.

## Testes

```bash
.venv/bin/python -m pytest
```

53 testes, incluindo empate, evidência não-diagnóstica, evidência decisiva, piso absoluto da
margem, validação, CLI, MCP e contenção de symlink.

## Licença

MIT. Contribuições: [CONTRIBUTING.md](CONTRIBUTING.md). Segurança: [SECURITY.md](SECURITY.md).
