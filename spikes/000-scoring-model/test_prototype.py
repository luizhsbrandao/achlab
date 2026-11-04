import copy
import json
from pathlib import Path

import pytest

import prototype as p

CASE = json.loads(Path(__file__).with_name("case.json").read_text(encoding="utf-8"))


def test_pesos():
    e1 = next(e for e in CASE["evidence"] if e["id"] == "E1")
    e6 = next(e for e in CASE["evidence"] if e["id"] == "E6")
    assert p.weight(e1) == pytest.approx(0.85)
    assert p.weight(e6) == pytest.approx(0.018)


def test_ranking_principal():
    r = p.rank(CASE)
    assert [x["id"] for x in r["rows"]] == ["H1", "H3", "H2"]
    assert r["rows"][0]["I"] == pytest.approx(0.0)
    assert r["rows"][1]["I"] == pytest.approx(2.0)
    assert r["rows"][2]["I"] == pytest.approx(3.53)
    assert r["tie"] is False
    assert r["margin_abs"] == pytest.approx(2.0)


def test_nao_diagnostica_nao_muda_ranking():
    without = copy.deepcopy(CASE)
    without["evidence"] = [e for e in without["evidence"] if e["id"] != "E4"]
    base, alt = p.rank(CASE), p.rank(without)
    assert [x["I"] for x in base["rows"]] == pytest.approx([x["I"] for x in alt["rows"]])
    assert [x["id"] for x in base["rows"]] == [x["id"] for x in alt["rows"]]
    e4 = next(e for e in CASE["evidence"] if e["id"] == "E4")
    assert p.diagnosticity(e4, ["H1", "H2", "H3"]) == 0.0


def test_leave_one_out_acha_decisiva():
    loo = p.leave_one_out(CASE)
    assert loo["decisive"] == ["E7"]
    assert loo["preserved"] == 8
    assert loo["robustness"] == pytest.approx(8 / 9)


def test_empate_vira_indeterminado():
    case = {
        "question": "x",
        "hypotheses": [{"id": "H1"}, {"id": "H2"}],
        "evidence": [
            {
                "id": "E1",
                "reliability": "A",
                "credibility": 1,
                "relevance": "alta",
                "source": "s",
                "excerpt": "e",
                "locator": "l",
                "assessments": {"H1": "+", "H2": "+"},
            }
        ],
    }
    r = p.rank(case)
    assert r["tie"] is True
    band, _ = p.confidence(case, r, p.leave_one_out(case), p.provenance(case))
    assert band == "INDETERMINADA"


def test_margem_relativa_sozinha_mente():
    def neutral(eid):
        return {
            "id": eid,
            "reliability": "A",
            "credibility": 1,
            "relevance": "alta",
            "source": "s",
            "excerpt": "e",
            "locator": "l",
            "assessments": {"H1": "0", "H2": "0"},
        }

    case = {
        "question": "x",
        "hypotheses": [{"id": "H1"}, {"id": "H2"}],
        "evidence": [
            neutral("E1"),
            neutral("E2"),
            neutral("E3"),
            {
                "id": "E4",
                "reliability": "E",
                "credibility": 5,
                "relevance": "media",
                "source": "s",
                "excerpt": "e",
                "locator": "l",
                "assessments": {"H1": "--", "H2": "0"},
            },
        ],
    }
    r = p.rank(case)
    assert r["margin_abs"] == pytest.approx(0.036)
    assert r["margin_rel"] == pytest.approx(1.0)
    loo = p.leave_one_out(case)
    assert loo["preserved"] == 3
    assert loo["robustness"] == pytest.approx(0.75)
    band_floor, detail = p.confidence(case, r, loo, p.provenance(case), floor=0.10)
    band_spec, _ = p.confidence(case, r, loo, p.provenance(case), floor=0.0)
    assert detail["margin_abs"] < 0.10
    assert band_floor == "BAIXA"
    assert band_spec == "MODERADA"
