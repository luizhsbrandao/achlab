import json

import pytest

from achlab.demo import build_demo
from achlab.model import (
    Assessment as A,
    Hypothesis,
    Project,
    Source,
    validate,
)


def test_source_has_locator():
    assert Source(url="https://x").has_locator()
    assert Source(archive_url="https://web.archive/x").has_locator()
    assert Source(locator="p. 42").has_locator()
    assert not Source(citation="só citação").has_locator()


def test_roundtrip_dict():
    demo = build_demo()
    data = json.loads(json.dumps(demo.to_dict(), ensure_ascii=False))
    assert Project.from_dict(data).to_dict() == demo.to_dict()


def test_demo_e_valido():
    assert validate(build_demo()) == []


def test_pergunta_vazia():
    demo = build_demo()
    demo.question = "  "
    assert "pergunta vazia" in validate(demo)


def test_ids_duplicados():
    demo = build_demo()
    demo.hypotheses.append(Hypothesis(id="H1", statement="duplicada"))
    assert "ids de hipótese duplicados" in validate(demo)


def test_evidencia_aceita_sem_citacao():
    demo = build_demo()
    demo.evidence[0].source.citation = ""
    assert any("sem citação" in e for e in validate(demo))


def test_evidencia_aceita_sem_trecho():
    demo = build_demo()
    demo.evidence[0].excerpt = ""
    assert any("sem trecho" in e for e in validate(demo))


def test_evidencia_aceita_sem_localizador():
    demo = build_demo()
    demo.evidence[0].source = Source(citation="citação")
    assert any("sem localizador" in e for e in validate(demo))


def test_avaliacao_sem_justificativa():
    demo = build_demo()
    demo.evidence[0].assessments["H1"] = A(consistency="++", rationale="")
    assert any("sem justificativa" in e for e in validate(demo))


def test_avaliacao_hipotese_inexistente():
    demo = build_demo()
    demo.evidence[0].assessments["H9"] = A(consistency="+", rationale="r")
    assert any("hipótese inexistente" in e for e in validate(demo))


def test_hipotese_rejeitada_sem_motivo():
    demo = build_demo()
    demo.hypotheses[0].status = "rejeitada"
    demo.hypotheses[0].rejection_reason = ""
    assert any("sem motivo" in e for e in validate(demo))


def test_escalas_invalidas():
    demo = build_demo()
    demo.evidence[0].reliability = "Z"
    demo.evidence[0].credibility = 9
    demo.evidence[0].relevance = "x"
    errors = validate(demo)
    assert any("confiabilidade inválida" in e for e in errors)
    assert any("credibilidade inválida" in e for e in errors)
    assert any("relevância inválida" in e for e in errors)


def test_sem_hipotese_ativa():
    demo = build_demo()
    for h in demo.hypotheses:
        h.status = "rejeitada"
        h.rejection_reason = "motivo"
    assert "projeto sem hipótese ativa" in validate(demo)


def test_consistencia_invalida():
    demo = build_demo()
    demo.evidence[0].assessments["H1"] = A(consistency="?", rationale="r")
    assert any("consistência inválida" in e for e in validate(demo))
