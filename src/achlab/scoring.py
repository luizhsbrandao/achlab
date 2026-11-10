"""Pontuação determinística do ACH.

Regras da spec do projeto (§5), com a correção do spike M0:
a faixa exige margem absoluta **e** relativa.
"""
from __future__ import annotations

from .model import Evidence, Project

WEIGHTS = {
    "reliability": {"A": 1.00, "B": 0.80, "C": 0.60, "D": 0.40, "E": 0.20, "F": 0.50},
    "credibility": {1: 1.00, 2: 0.85, 3: 0.65, 4: 0.40, 5: 0.15, 6: 0.50},
    "relevance": {"alta": 1.00, "media": 0.60, "baixa": 0.25},
}
SIGN_VALUE = {"++": 2, "+": 1, "0": 0, "-": -1, "--": -2}
NEGATIVE = {"-": 1, "--": 2}
SUPPORTIVE = {"+": 1, "++": 2}
TOL = 1e-9
MARGIN_FLOOR = 0.10
DIAG_MIN = 0.20


def weight(ev: Evidence) -> float:
    return (
        WEIGHTS["reliability"][ev.reliability]
        * WEIGHTS["credibility"][ev.credibility]
        * WEIGHTS["relevance"][ev.relevance]
    )


def _values(ev: Evidence, hypothesis_ids: list[str]) -> list[int]:
    return [
        SIGN_VALUE[ev.consistency(h)]
        for h in hypothesis_ids
        if ev.consistency(h) != "na"
    ]


def inconsistency(hypothesis_id: str, evidence: list[Evidence]) -> float:
    total = 0.0
    for ev in evidence:
        raw = ev.consistency(hypothesis_id)
        if raw in NEGATIVE:
            total += weight(ev) * NEGATIVE[raw]
    return total


def support(hypothesis_id: str, evidence: list[Evidence]) -> float:
    total = 0.0
    for ev in evidence:
        raw = ev.consistency(hypothesis_id)
        if raw in SUPPORTIVE:
            total += weight(ev) * SUPPORTIVE[raw]
    return total


def diagnosticity(ev: Evidence, hypothesis_ids: list[str]) -> float:
    values = _values(ev, hypothesis_ids)
    if len(values) < 2:
        return 0.0
    return (max(values) - min(values)) / 4.0


def _rank(project: Project, evidence: list[Evidence]) -> dict:
    hypothesis_ids = [h.id for h in project.active_hypotheses()]
    rows = [
        {
            "id": hid,
            "I": inconsistency(hid, evidence),
            "S": support(hid, evidence),
        }
        for hid in hypothesis_ids
    ]
    rows.sort(key=lambda r: (r["I"], r["id"]))
    tie = len(rows) >= 2 and abs(rows[0]["I"] - rows[1]["I"]) < TOL
    margin_abs = (rows[1]["I"] - rows[0]["I"]) if len(rows) >= 2 else 0.0
    margin_rel = margin_abs / max(rows[1]["I"], 1e-9) if len(rows) >= 2 else 0.0
    return {
        "rows": rows,
        "tie": tie,
        "margin_abs": margin_abs,
        "margin_rel": margin_rel,
    }


def rank(project: Project) -> dict:
    return _rank(project, project.accepted_evidence())


def leave_one_out(project: Project) -> dict:
    evidence = project.accepted_evidence()
    base = _rank(project, evidence)
    base_top = None if base["tie"] or not base["rows"] else base["rows"][0]["id"]
    decisive: list[str] = []
    preserved = 0
    for i in range(len(evidence)):
        subset = [e for j, e in enumerate(evidence) if j != i]
        result = _rank(project, subset)
        top = None if result["tie"] or not result["rows"] else result["rows"][0]["id"]
        if top is not None and top == base_top:
            preserved += 1
        else:
            decisive.append(evidence[i].id)
    n = len(evidence)
    return {
        "runs": n,
        "preserved": preserved,
        "robustness": preserved / n if n else 0.0,
        "decisive": decisive,
    }


def provenance(project: Project) -> float:
    evidence = project.evidence
    if not evidence:
        return 0.0
    ok = sum(
        1
        for e in evidence
        if e.status == "aceita"
        and e.source.citation.strip()
        and e.excerpt.strip()
        and e.source.has_locator()
    )
    return ok / len(evidence)


def evaluate(project: Project) -> dict:
    """Recebe `Project`; devolve dict com `ranking`, `leave_one_out`, `provenance`, `confidence` e `detail`."""
    result = rank(project)
    loo = leave_one_out(project)
    prov = provenance(project)
    band, detail = confidence(project, result, loo, prov)
    return {
        "ranking": result,
        "leave_one_out": loo,
        "provenance": prov,
        "confidence": band,
        "detail": detail,
    }


def confidence(project: Project, result: dict, loo: dict, prov: float) -> tuple[str, dict]:
    hypothesis_ids = [h.id for h in project.active_hypotheses()]
    diagnostic = sum(
        1
        for e in project.accepted_evidence()
        if diagnosticity(e, hypothesis_ids) >= DIAG_MIN
    )
    detail = {
        "diagnostic": diagnostic,
        "provenance": prov,
        "margin_abs": result["margin_abs"],
        "margin_rel": result["margin_rel"],
        **loo,
    }
    if len(hypothesis_ids) < 2 or diagnostic == 0 or prov < 0.3 or result["tie"]:
        return "INDETERMINADA", detail
    if (
        loo["robustness"] >= 0.90
        and result["margin_rel"] >= 0.25
        and result["margin_abs"] >= MARGIN_FLOOR
        and prov >= 0.80
        and diagnostic >= 3
    ):
        return "ALTA", detail
    if (
        loo["robustness"] >= 0.70
        and result["margin_rel"] >= 0.10
        and result["margin_abs"] >= MARGIN_FLOOR
        and prov >= 0.50
    ):
        return "MODERADA", detail
    return "BAIXA", detail
