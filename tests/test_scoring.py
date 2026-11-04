import copy

import pytest

from achlab.demo import build_demo
from achlab.model import Assessment, Evidence, Hypothesis, Project, Source
from achlab.scoring import (
    MARGIN_FLOOR,
    confidence,
    diagnosticity,
    inconsistency,
    leave_one_out,
    provenance,
    rank,
    support,
    weight,
)


def make_evidence(
    eid: str,
    consistency: dict[str, str] | None = None,
    reliability: str = "A",
    credibility: int = 1,
    relevance: str = "alta",
    status: str = "aceita",
) -> Evidence:
    assessments = {
        hid: Assessment(consistency=c, rationale="r")
        for hid, c in (consistency or {}).items()
    }
    return Evidence(
        id=eid,
        title=eid,
        source=Source(citation="c", locator="fixture://" + eid),
        reliability=reliability,
        credibility=credibility,
        relevance=relevance,
        excerpt="e",
        status=status,
        assessments=assessments,
    )


def test_pesos():
    demo = build_demo()
    assert weight(demo.evidence[0]) == pytest.approx(0.85)
    e6 = next(e for e in demo.evidence if e.id == "E6")
    assert weight(e6) == pytest.approx(0.018)


def test_diagnosticidade():
    demo = build_demo()
    assert diagnosticity(demo.evidence[0], ["H1", "H2", "H3"]) == pytest.approx(0.75)
    e4 = next(e for e in demo.evidence if e.id == "E4")
    assert diagnosticity(e4, ["H1", "H2", "H3"]) == 0.0


def test_ranking_demo():
    result = rank(build_demo())
    assert [r["id"] for r in result["rows"]] == ["H1", "H3", "H2"]
    assert result["rows"][0]["I"] == pytest.approx(0.0)
    assert result["rows"][1]["I"] == pytest.approx(2.0)
    assert result["rows"][2]["I"] == pytest.approx(3.53)
    assert result["tie"] is False
    assert result["margin_abs"] == pytest.approx(2.0)


def test_nao_diagnostica_nao_muda_ranking():
    demo = build_demo()
    without = copy.deepcopy(demo)
    without.evidence = [e for e in without.evidence if e.id != "E4"]
    base, alt = rank(demo), rank(without)
    assert [r["I"] for r in base["rows"]] == pytest.approx([r["I"] for r in alt["rows"]])
    assert [r["id"] for r in base["rows"]] == [r["id"] for r in alt["rows"]]


def test_leave_one_out_acha_decisiva():
    loo = leave_one_out(build_demo())
    assert loo["decisive"] == ["E7"]
    assert loo["preserved"] == 8
    assert loo["robustness"] == pytest.approx(8 / 9)


def test_empate_vira_indeterminado():
    project = Project(
        question="q",
        hypotheses=[Hypothesis("H1", "a"), Hypothesis("H2", "b")],
        evidence=[make_evidence("E1", {"H1": "+", "H2": "+"})],
    )
    result = rank(project)
    assert result["tie"] is True
    band, _ = confidence(project, result, leave_one_out(project), provenance(project))
    assert band == "INDETERMINADA"


def test_piso_absoluto_da_margem():
    project = Project(
        question="q",
        hypotheses=[Hypothesis("H1", "a"), Hypothesis("H2", "b")],
        evidence=[
            make_evidence("E1", {"H1": "0", "H2": "0"}),
            make_evidence("E2", {"H1": "0", "H2": "0"}),
            make_evidence("E3", {"H1": "0", "H2": "0"}),
            make_evidence(
                "E4", {"H1": "--", "H2": "0"}, reliability="E", credibility=5, relevance="media"
            ),
        ],
    )
    result = rank(project)
    assert result["margin_abs"] == pytest.approx(0.036)
    assert result["margin_rel"] == pytest.approx(1.0)
    loo = leave_one_out(project)
    assert loo["preserved"] == 3
    assert loo["robustness"] == pytest.approx(0.75)
    band, _ = confidence(project, result, loo, provenance(project))
    assert MARGIN_FLOOR == 0.10
    assert band == "BAIXA"


def test_proveniencia_conta_drafts():
    demo = build_demo()
    demo.evidence[0].status = "draft"
    assert provenance(demo) == pytest.approx(8 / 9)


def test_suporte_nao_ranqueia():
    demo = build_demo()
    base = rank(demo)
    before_support = support("H1", demo.accepted_evidence())
    demo.evidence.append(
        make_evidence("E10", {"H1": "++", "H2": "++", "H3": "++"})
    )
    after = rank(demo)
    assert [r["I"] for r in base["rows"]] == pytest.approx([r["I"] for r in after["rows"]])
    assert all(
        after["rows"][i]["S"] > base["rows"][i]["S"] for i in range(len(base["rows"]))
    )
    assert support("H1", demo.accepted_evidence()) > before_support


def test_uma_hipotese_e_indeterminada():
    project = Project(
        question="q",
        hypotheses=[Hypothesis("H1", "a")],
        evidence=[make_evidence("E1", {"H1": "+"})],
    )
    result = rank(project)
    band, _ = confidence(project, result, leave_one_out(project), provenance(project))
    assert band == "INDETERMINADA"


def test_sem_evidencia_e_indeterminada():
    project = Project(
        question="q",
        hypotheses=[Hypothesis("H1", "a"), Hypothesis("H2", "b")],
    )
    result = rank(project)
    assert result["tie"] is True
    band, _ = confidence(project, result, leave_one_out(project), provenance(project))
    assert band == "INDETERMINADA"
    assert provenance(project) == 0.0


def test_leave_one_out_sem_evidencia():
    project = Project(
        question="q",
        hypotheses=[Hypothesis("H1", "a"), Hypothesis("H2", "b")],
    )
    loo = leave_one_out(project)
    assert loo["runs"] == 0
    assert loo["robustness"] == 0.0
    assert loo["decisive"] == []


def test_inconsistencia_e_suporte():
    demo = build_demo()
    assert inconsistency("H1", demo.accepted_evidence()) == pytest.approx(0.0)
    assert inconsistency("H2", demo.accepted_evidence()) == pytest.approx(3.53)
    assert support("H1", demo.accepted_evidence()) == pytest.approx(2.1275)
