#!/usr/bin/env python3
"""Spike M0 do achlab: valida o modelo de pontuação da spec.

Código descartável. Não é o pacote `achlab`. Responde:
1. O ranking por menor inconsistência separa as hipóteses no caso sintético?
2. Evidência não-diagnóstica muda o ranking? (deve ser não)
3. A sensibilidade leave-one-out identifica a evidência decisiva?
4. Empate vira INDETERMINADO?
5. A margem relativa sozinha mente? (caso quase-empate)
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

WEIGHTS = {
    "reliability": {"A": 1.00, "B": 0.80, "C": 0.60, "D": 0.40, "E": 0.20, "F": 0.50},
    "credibility": {1: 1.00, 2: 0.85, 3: 0.65, 4: 0.40, 5: 0.15, 6: 0.50},
    "relevance": {"alta": 1.00, "media": 0.60, "baixa": 0.25},
}
SIGN_VALUE = {"++": 2, "+": 1, "0": 0, "-": -1, "--": -2}
NEGATIVE = {"-": 1, "--": 2}
SUPPORTIVE = {"+": 1, "++": 2}
TOL = 1e-9


def weight(ev: dict) -> float:
    return (
        WEIGHTS["reliability"][ev["reliability"]]
        * WEIGHTS["credibility"][int(ev["credibility"])]
        * WEIGHTS["relevance"][ev["relevance"]]
    )


def assessments_for(ev: dict, hypotheses: list[str]) -> dict[str, int]:
    out = {}
    for h in hypotheses:
        raw = ev["assessments"].get(h, "na")
        if raw != "na":
            out[h] = SIGN_VALUE[raw]
    return out


def inconsistency(hypothesis: str, evidence: list[dict]) -> float:
    total = 0.0
    for ev in evidence:
        raw = ev["assessments"].get(hypothesis, "na")
        if raw in NEGATIVE:
            total += weight(ev) * NEGATIVE[raw]
    return total


def support(hypothesis: str, evidence: list[dict]) -> float:
    total = 0.0
    for ev in evidence:
        raw = ev["assessments"].get(hypothesis, "na")
        if raw in SUPPORTIVE:
            total += weight(ev) * SUPPORTIVE[raw]
    return total


def diagnosticity(ev: dict, hypotheses: list[str]) -> float:
    values = list(assessments_for(ev, hypotheses).values())
    if len(values) < 2:
        return 0.0
    return (max(values) - min(values)) / 4.0


def rank(case: dict, evidence: list[dict] | None = None) -> dict:
    evs = case["evidence"] if evidence is None else evidence
    hyps = [h["id"] for h in case["hypotheses"]]
    rows = [{"id": h, "I": inconsistency(h, evs), "S": support(h, evs)} for h in hyps]
    rows.sort(key=lambda r: (r["I"], r["id"]))
    tie = len(rows) >= 2 and abs(rows[0]["I"] - rows[1]["I"]) < TOL
    margin_abs = (rows[1]["I"] - rows[0]["I"]) if len(rows) >= 2 else 0.0
    margin_rel = margin_abs / max(rows[1]["I"], 1e-9) if len(rows) >= 2 else 0.0
    return {"rows": rows, "tie": tie, "margin_abs": margin_abs, "margin_rel": margin_rel}


def leave_one_out(case: dict) -> dict:
    base = rank(case)
    base_top = None if base["tie"] else base["rows"][0]["id"]
    decisive = []
    preserved = 0
    for i in range(len(case["evidence"])):
        subset = [e for j, e in enumerate(case["evidence"]) if j != i]
        r = rank(case, subset)
        top = None if r["tie"] else r["rows"][0]["id"]
        if top is not None and top == base_top:
            preserved += 1
        else:
            decisive.append(case["evidence"][i]["id"])
    n = len(case["evidence"])
    return {
        "runs": n,
        "preserved": preserved,
        "robustness": preserved / n if n else 0.0,
        "decisive": decisive,
    }


def provenance(case: dict) -> float:
    evs = case["evidence"]
    if not evs:
        return 0.0
    ok = sum(1 for e in evs if e.get("source") and e.get("excerpt") and e.get("locator"))
    return ok / len(evs)


def confidence(case: dict, r: dict, loo: dict, prov: float, floor: float = 0.10) -> tuple[str, dict]:
    """Faixa de confiança. `floor` é o piso absoluto da margem.

    floor=0 reproduz a regra original da spec (só margem relativa), para comparação.
    """
    hyps = [h["id"] for h in case["hypotheses"]]
    diag = sum(1 for e in case["evidence"] if diagnosticity(e, hyps) >= 0.2)
    detail = {
        "diagnostic": diag,
        "provenance": prov,
        "margin_abs": r["margin_abs"],
        "margin_rel": r["margin_rel"],
        **loo,
    }
    if len(hyps) < 2 or diag == 0 or prov < 0.3 or r["tie"]:
        return "INDETERMINADA", detail
    if (
        loo["robustness"] >= 0.90
        and r["margin_rel"] >= 0.25
        and r["margin_abs"] >= floor
        and prov >= 0.80
        and diag >= 3
    ):
        return "ALTA", detail
    if (
        loo["robustness"] >= 0.70
        and r["margin_rel"] >= 0.10
        and r["margin_abs"] >= floor
        and prov >= 0.50
    ):
        return "MODERADA", detail
    return "BAIXA", detail


def report(case: dict) -> str:
    hyps = [h["id"] for h in case["hypotheses"]]
    r = rank(case)
    loo = leave_one_out(case)
    prov = provenance(case)
    band, detail = confidence(case, r, loo, prov, floor=0.10)
    band_spec, _ = confidence(case, r, loo, prov, floor=0.0)

    lines = [f"# {case['question']}", ""]
    lines.append("| Evidência | w | D | " + " | ".join(hyps) + " |")
    lines.append("|---|---|---|" + "---|" * len(hyps))
    for e in case["evidence"]:
        cells = [e["assessments"].get(h, "na") for h in hyps]
        lines.append(
            f"| {e['id']} | {weight(e):.3f} | {diagnosticity(e, hyps):.2f} | "
            + " | ".join(cells)
            + " |"
        )

    lines += ["", "## Ranking (menor inconsistência)", ""]
    lines.append("| # | Hipótese | I | S |")
    lines.append("|---|---|---|---|")
    for i, row in enumerate(r["rows"], 1):
        lines.append(f"| {i} | {row['id']} | {row['I']:.3f} | {row['S']:.3f} |")

    lines += [""]
    lines.append(f"- Empate: {'sim' if r['tie'] else 'não'}")
    lines.append(f"- Margem absoluta: {r['margin_abs']:.3f}")
    lines.append(f"- Margem relativa: {r['margin_rel']:.3f}")
    lines.append(
        f"- Robustez: {loo['robustness']:.3f} ({loo['preserved']}/{loo['runs']}); "
        f"decisivas: {', '.join(loo['decisive']) or 'nenhuma'}"
    )
    lines.append(f"- Proveniência: {prov:.2f}")
    lines.append(f"- Faixa com piso absoluto de 0,10: **{band}** (diagnósticas: {detail['diagnostic']})")
    lines.append(f"- Faixa pela regra original da spec (só relativa): **{band_spec}**")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Spike M0 do achlab")
    parser.add_argument("case", nargs="?", default=Path(__file__).with_name("case.json"))
    args = parser.parse_args()
    case = json.loads(Path(args.case).read_text(encoding="utf-8"))
    print(report(case))


if __name__ == "__main__":
    main()
