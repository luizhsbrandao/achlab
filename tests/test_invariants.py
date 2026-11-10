# -*- coding: utf-8 -*-
"""Invariantes do vocabulário — o teste que impede a dessincronia silenciosa.

O mapa do repo (09/11/2026) apontou dois riscos de manutenção medidos no código:

1. `CONSISTENCIES` vive em `model.py`, mas o `choices` do argparse repete a lista literal
   em `cli.py` — nível novo em um lugar e não no outro passa em silêncio, porque cada camada
   valida contra a própria lista.
2. `WEIGHTS` em `scoring.py` é indexado por chave dura: valor novo em `RELIABILITIES` /
   `CREDIBILITIES` / `RELEVANCES` sem entrada em `WEIGHTS` quebra com `KeyError` em runtime,
   longe do ponto de validação.

Aqui o vocabulário é comparado entre módulos. Nada de comportamento: se este arquivo fica
vermelho, alguém mudou um enum sem mudar o consumidor.
"""
from achlab import model
from achlab.cli import build_parser
from achlab.scoring import NEGATIVE, SIGN_VALUE, SUPPORTIVE, WEIGHTS

CASAS = {
    "reliability": model.RELIABILITIES,
    "credibility": model.CREDIBILITIES,
    "relevance": model.RELEVANCES,
}


def test_weights_cobre_exatamente_o_vocabulario_do_modelo():
    """Toda chave de `WEIGHTS` existe no modelo, e todo valor do modelo tem peso."""
    for campo, valores in CASAS.items():
        assert set(WEIGHTS[campo]) == set(valores), (
            f"WEIGHTS['{campo}'] e model.{campo.upper()} divergiram: "
            f"faltando em WEIGHTS={set(valores) - set(WEIGHTS[campo])}, "
            f"sobrando em WEIGHTS={set(WEIGHTS[campo]) - set(valores)}"
        )


def test_vocabulario_de_consistencia_e_unico():
    """`na` não pontua; todo o resto de `CONSISTENCIES` precisa de valor em `SIGN_VALUE`."""
    assert set(SIGN_VALUE) | {"na"} == model.CONSISTENCIES
    assert set(NEGATIVE) | set(SUPPORTIVE) <= set(SIGN_VALUE)
    assert not set(NEGATIVE) & set(SUPPORTIVE)


def _todas_as_acoes(parser):
    """Percorre o parser recursivamente (subcomando dentro de subcomando também conta)."""
    for action in parser._actions:
        yield action
        sub = getattr(action, "choices", None)
        if isinstance(sub, dict):
            for filho in sub.values():
                yield from _todas_as_acoes(filho)


def test_argparse_nao_repete_o_vocabulario_por_fora():
    """As escolhas da CLI têm de sair do modelo, não de uma lista literal paralela."""
    escolhas = {act.dest: set(act.choices)
                for act in _todas_as_acoes(build_parser())
                if act.dest in {"consistency", "reliability", "credibility", "relevance"}
                and act.choices is not None}

    assert escolhas["consistency"] == model.CONSISTENCIES
    assert escolhas["reliability"] == model.RELIABILITIES
    assert escolhas["credibility"] == model.CREDIBILITIES
    assert escolhas["relevance"] == model.RELEVANCES
