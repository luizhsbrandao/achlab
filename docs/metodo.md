# Method

`achlab` implements **Analysis of Competing Hypotheses** (ACH), the structured analytic technique
described by Richards Heuer. The core idea is counter-intuitive: you do not rank hypotheses by
how much evidence supports them. You rank them by **how little evidence contradicts them**.

## The analysis loop

1. **Frame the question.** One question, one scope. The tool stores the question verbatim.
2. **List mutually exclusive hypotheses.** At least two active hypotheses are required for a
   meaningful ranking. A rejected hypothesis keeps its reason; it is not deleted.
3. **Collect evidence with provenance.** Each item needs a citation, an excerpt and a locator
   (URL, archive or page). Items enter as `draft`; `ach ev accept` enforces the gate.
4. **Assess consistency.** For each evidence × hypothesis pair, the analyst chooses `++`, `+`,
   `0`, `-` or `--`, and writes a rationale. `na` means "not assessed" and is excluded.
5. **Rank.** The tool computes the weighted inconsistency `I(h)` and sorts ascending. The least
   inconsistent hypothesis is the one that survives. Support `S(h)` is reported but never used
   to rank: evidence consistent with every hypothesis is non-diagnostic.
6. **Test robustness.** Each accepted item is removed in turn; if the leader changes, the item is
   flagged as decisive. The fraction of runs that preserve the leader is the robustness.
7. **Report.** Matrix, ranking, margins, robustness, sources, gaps. No probability language.

## Diagnostic evidence

Evidence that is consistent with every hypothesis has zero diagnosticity and cannot separate
them. Evidence that is inconsistent with one hypothesis and consistent with the others is
diagnostic. The report prints `D(e) = (max − min) / 4` over the assessments, and marks items
below `0.20` as non-discriminating.

## What the tool refuses to do

- Generate judgments with an LLM. An optional adapter may draft text, but every item requires a
  human acceptance with a source.
- Output probabilities. The confidence band describes the **robustness of the analysis**, not
  the probability of a hypothesis.
- Produce a citable report with incomplete provenance. It exits `3`, unless the analyst
  explicitly asks for a watermarked `NÃO CITÁVEL` version.
- Store classified information or PII. The tool is for unclassified, public-source analysis.

## Key Assumptions Check

Assumptions are stored with the project (`statement`, `why_it_matters`, `test`, `status`) and
printed in the report. They are not scored: an untested assumption is a gap, not a number.
