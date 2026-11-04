# Spike 000 — modelo de pontuação

## Pergunta

O modelo da spec (pesos explícitos, ranking por menor inconsistência, diagnosticidade,
leave-one-out) produz um ranking defensável num caso sintético — e falha de forma visível
quando deve falhar?

## Como rodar

Da raiz do repo:

```bash
python3 -m venv .venv
.venv/bin/pip install pytest
.venv/bin/python -m pytest spikes/000-scoring-model -q
.venv/bin/python spikes/000-scoring-model/prototype.py
```

## Resultado (2026-11-04, Python 3.13.5)

Caso sintético com 3 hipóteses e 9 evidências:

| Evidência | w | D | H1 | H2 | H3 |
|---|---|---|---|---|---|
| E1 log de crachá | 0.850 | 0.75 | ++ | - | 0 |
| E2 VPN encerrada | 1.000 | 0.50 | 0 | -- | 0 |
| E3 falha conhecida | 0.680 | 0.50 | 0 | + | ++ |
| E4 post no fórum | 0.312 | 0.00 | + | + | + |
| E5 conta descartável | 0.144 | 0.00 | 0 | 0 | 0 |
| E6 denúncia anônima | 0.018 | 0.25 | + | 0 | 0 |
| E7 correção aplicada | 1.000 | 0.50 | 0 | 0 | -- |
| E8 insatisfação | 0.098 | 0.25 | + | 0 | 0 |
| E9 prestador sem entrada | 0.680 | 0.25 | 0 | - | 0 |

Ranking: **H1 (I=0.000) → H3 (I=2.000) → H2 (I=3.530)**.
Margem absoluta 2.000; relativa 1.000. Robustez 0.889 (8/9), com **E7 decisiva**.
Diagnósticas: 7. Proveniência 1.00. Faixa: **MODERADA**.

## Testes (6 passed)

- Ranking principal e pesos exatos.
- Evidência não-diagnóstica (E4, D=0) não muda nenhum I nem a ordem.
- Leave-one-out isola E7: sem ela, H1 e H3 empatam em 0.
- Empate vira `INDETERMINADA`.
- Caso quase-empate expõe a falha da margem relativa (abaixo).

## Verdict: VALIDATED (com uma correção)

### What worked

- O ranking separa as três hipóteses e a matriz deixa o cálculo auditável.
- A diagnosticidade funciona: E4 e E5 (D=0) não mexem no resultado.
- O leave-one-out encontra exatamente a evidência que sustenta a conclusão (E7).
- O modelo **não** superestima: 8/9 derruba a faixa de ALTA para MODERADA, o que é honesto —
  a separação entre H1 e H3 depende de uma única fonte.

### What didn't

- **Margem relativa sozinha mente.** No caso quase-empate, um gap absoluto de 0,036 (peso de
  uma fonte E5) com I≈0,036 dá margem relativa 1,0. Pela regra original da spec, a faixa seria
  MODERADA; com piso absoluto de 0,10, é BAIXA. O piso é obrigatório.

### Surprises

- A robustez de 0,889 cai por 0,011 abaixo do corte de 0,90 da faixa ALTA. O corte funciona,
  mas casos com 9 evidências ficam sensíveis a um único leave-one-out; a spec deve dizer que
  o corte é sobre a fração, não sobre uma contagem.
- E7 é a única evidência que separa H1 de H3 — e é justamente a de peso máximo (A1). O relatório
  precisa destacar isso, não esconder atrás do ranking.

### Recommendation for the real build

1. Fixar o piso absoluto de 0,10 na margem (spec §5 e faixas).
2. Manter os pesos; nenhum ajuste necessário no caso.
3. M1 pode começar: o núcleo é determinístico e os testes de propriedade já cobrem os modos de
   falha que importam.
