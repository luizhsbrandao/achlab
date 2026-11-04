# Scoring

All formulas are deterministic and visible in the report. Weights live in
`src/achlab/scoring.py`; the rationale is below.

## Weights

```
w(e) = r(reliability) × c(credibility) × rel(relevance)
```

| Reliability (Admiralty) | Weight | Credibility | Weight | Relevance | Weight |
|---|---|---|---|---|---|
| A — completely reliable | 1.00 | 1 — confirmed | 1.00 | high | 1.00 |
| B — usually reliable | 0.80 | 2 — probably true | 0.85 | medium | 0.60 |
| C — fairly reliable | 0.60 | 3 — possibly true | 0.65 | low | 0.25 |
| D — not usually reliable | 0.40 | 4 — doubtful | 0.40 | | |
| E — unreliable | 0.20 | 5 — improbable | 0.15 | | |
| F — cannot be judged | 0.50 | 6 — cannot be judged | 0.50 | | |

`F` and `6` are not zero: an unrated source still counts as evidence, but the report flags it.
The weights are explicit priors, not truth; sensitivity analysis shows what depends on them.

## Inconsistency and support

For each active hypothesis `h` and accepted evidence `e`:

```
I(h) = Σ w(e) × s(c)   for c ∈ {-, --}, s(-)=1, s(--)=2
S(h) = Σ w(e) × s(c)   for c ∈ {+, ++}, s(+)=1, s(++)=2
```

The ranking is ascending `I(h)`. `S(h)` is printed but never used to rank: supportive evidence
that applies to every hypothesis inflates support without discriminating.

## Diagnosticity

```
D(e) = (max assessment − min assessment) / 4
```

Assessments map to `++ = 2`, `+ = 1`, `0 = 0`, `- = -1`, `-- = -2`; `na` is excluded. `D ≥ 0.20`
is diagnostic. `D = 0` means the item is consistent (or neutral) everywhere and cannot separate
the hypotheses.

## Margins and robustness

```
margin_abs = I(2nd) − I(1st)
margin_rel = margin_abs / max(I(2nd), 0.001)
robustness = share of leave-one-out runs that preserve the leader
```

A tie (`margin_abs < 0.001`) yields `INDETERMINADO`; the tool never breaks a tie by ordering.
Leave-one-out removes one accepted item at a time and recomputes the ranking. Items whose removal
changes the leader are listed as **decisive**.

**Why both margins?** A relative margin alone lies when the total is tiny. In the validated
fixture, a gap of `0.036` over `I≈0.036` gives a relative margin of `1.0` — apparently decisive,
actually the weight of one unreliable source. The confidence band therefore requires
`margin_abs ≥ 0.10` **and** the relative threshold.

## Confidence band

The band describes the analysis, not the hypothesis:

| Band | Rule |
|---|---|
| `INDETERMINADA` | fewer than 2 active hypotheses, no diagnostic evidence, provenance < 30%, or a tie |
| `ALTA` | robustness ≥ 0.90 · relative margin ≥ 0.25 · absolute margin ≥ 0.10 · provenance ≥ 0.80 · ≥ 3 diagnostic items |
| `MODERADA` | robustness ≥ 0.70 · relative margin ≥ 0.10 · absolute margin ≥ 0.10 · provenance ≥ 0.50 |
| `BAIXA` | otherwise |

Provenance is `accepted items with citation + excerpt + locator / all items`.

## Worked example (the demo fixture)

Weights: `E1 = 1.00 × 0.85 × 1.00 = 0.850`; `E2 = 1.000`; `E7 = 1.000`.

```
I(H1) = 0.000
I(H3) = E7 (--) = 1.000 × 2 = 2.000
I(H2) = E1 (-) 0.850 + E2 (--) 2.000 + E9 (-) 0.680 = 3.530
```

Ranking: `H1 → H3 → H2`; `margin_abs = 2.000`, `margin_rel = 1.000`.

Leave-one-out: removing `E7` leaves `H1 = 0` and `H3 = 0` — a tie. `E7` is decisive, and
`robustness = 8/9 = 0.889`. The band is `MODERADA`: the margin and provenance are strong, but
the conclusion depends on one item, so `ALTA` (robustness ≥ 0.90) is refused.
