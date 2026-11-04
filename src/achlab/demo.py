"""Caso sintético embarcado, usado por `ach demo` e pelos testes."""
from __future__ import annotations

from .model import Assessment, Evidence, Hypothesis, Project, Source


def _ev(
    eid: str,
    title: str,
    citation: str,
    locator: str,
    excerpt: str,
    reliability: str,
    credibility: int,
    relevance: str,
    assessments: dict[str, tuple[str, str]],
) -> Evidence:
    return Evidence(
        id=eid,
        title=title,
        source=Source(citation=citation, locator=locator),
        reliability=reliability,
        credibility=credibility,
        relevance=relevance,
        excerpt=excerpt,
        status="aceita",
        assessments={
            hid: Assessment(consistency=consistency, rationale=rationale)
            for hid, (consistency, rationale) in assessments.items()
        },
    )


def build_demo() -> Project:
    hypotheses = [
        Hypothesis(
            id="H1",
            statement="Alguém do escritório financeiro divulgou o rascunho.",
            definition="Inclui acesso presencial ou remoto com credencial do financeiro.",
        ),
        Hypothesis(
            id="H2",
            statement="Um prestador externo acessou o arquivo pelo drive compartilhado.",
            definition="Acesso por VPN ou drive, sem entrada no prédio.",
        ),
        Hypothesis(
            id="H3",
            statement="O arquivo ficou exposto por falha de configuração do servidor.",
            definition="Leitura anônima no diretório legado.",
        ),
    ]
    evidence = [
        _ev(
            "E1",
            "Log de acesso após o expediente",
            "Log sintético de crachá",
            "fixture://log-cracha/2026-01-01",
            "Acesso ao andar financeiro às 22:14; único após as 20:00.",
            "A",
            2,
            "alta",
            {
                "H1": ("++", "Acesso presencial no horário do vazamento é o que H1 prevê."),
                "H2": ("-", "O prestador não tinha crachá para o andar financeiro."),
                "H3": ("0", "A falha de servidor não exige acesso presencial."),
            },
        ),
        _ev(
            "E2",
            "Sessão VPN do prestador encerrada antes do vazamento",
            "Log sintético de VPN",
            "fixture://log-vpn/2026-01-01",
            "Sessão do prestador terminou às 21:00; post no fórum às 23:40.",
            "A",
            1,
            "alta",
            {
                "H1": ("0", "Sem relação com o insider."),
                "H2": ("--", "O prestador estava desconectado 2h40 antes do post."),
                "H3": ("0", "A falha não depende de sessão do prestador."),
            },
        ),
        _ev(
            "E3",
            "Falha de configuração conhecida no servidor de arquivos",
            "Boletim sintético de infraestrutura",
            "fixture://boletim-infra/2026-01-01",
            "Servidor permitia leitura anônima em diretório legado.",
            "B",
            2,
            "alta",
            {
                "H1": ("0", "Sem relação com o insider."),
                "H2": ("+", "O prestador poderia usar a leitura anônima."),
                "H3": ("++", "É exatamente o mecanismo previsto por H3."),
            },
        ),
        _ev(
            "E4",
            "Post em fórum público",
            "Captura sintética do fórum",
            "fixture://forum/2026-01-01",
            "Rascunho apareceu às 23:40, 80 minutos após a saída do financeiro.",
            "B",
            3,
            "media",
            {
                "H1": ("+", "O horário é compatível com H1."),
                "H2": ("+", "O horário também é compatível com H2."),
                "H3": ("+", "O horário também é compatível com H3."),
            },
        ),
        _ev(
            "E5",
            "Conta do fórum criada com e-mail descartável",
            "Registro sintético do fórum",
            "fixture://forum/conta/2026-01-01",
            "Conta criada no mesmo dia, sem vínculo com identidade.",
            "C",
            4,
            "media",
            {
                "H1": ("0", "Não distingue as hipóteses."),
                "H2": ("0", "Não distingue as hipóteses."),
                "H3": ("0", "Não distingue as hipóteses."),
            },
        ),
        _ev(
            "E6",
            "Denúncia anônima",
            "Canal sintético de denúncia",
            "fixture://denuncia/2026-01-01",
            "Texto diz que 'alguém do financeiro' comentou o assunto.",
            "E",
            5,
            "media",
            {
                "H1": ("+", "Apoia H1, mas a fonte é não confiável."),
                "H2": ("0", "Não menciona o prestador."),
                "H3": ("0", "Não menciona falha de servidor."),
            },
        ),
        _ev(
            "E7",
            "Correção da falha aplicada antes do vazamento",
            "Registro sintético de mudanças",
            "fixture://mudancas/2026-01-01",
            "Correção aplicada três dias antes do post; leitura anônima bloqueada.",
            "A",
            1,
            "alta",
            {
                "H1": ("0", "Não trata do insider."),
                "H2": ("0", "Não trata do prestador."),
                "H3": ("--", "A falha já estava corrigida quando o arquivo apareceu."),
            },
        ),
        _ev(
            "E8",
            "Registro de insatisfação do servidor",
            "Extrato sintético de RH",
            "fixture://rh/2026-01-01",
            "Servidor do financeiro registrou insatisfação com a chefia no mês anterior.",
            "C",
            3,
            "baixa",
            {
                "H1": ("+", "Motivo fraco, mas compatível com H1."),
                "H2": ("0", "Não trata do prestador."),
                "H3": ("0", "Não trata de falha de servidor."),
            },
        ),
        _ev(
            "E9",
            "Prestador sem registro de entrada em 30 dias",
            "Log sintético de crachá",
            "fixture://log-cracha/prestador/2026-01-01",
            "Nenhuma entrada do prestador no período; acesso só remoto foi a VPN.",
            "B",
            2,
            "alta",
            {
                "H1": ("0", "Sem relação com o insider."),
                "H2": ("-", "O prestador não esteve no prédio no período."),
                "H3": ("0", "A falha não exige presença do prestador."),
            },
        ),
    ]
    return Project(
        question="Quem divulgou o rascunho de orçamento? (caso sintético)",
        scope="Demonstração; nenhum dado real.",
        analyst="achlab",
        created_at="2026-01-01T00:00:00+00:00",
        hypotheses=hypotheses,
        evidence=evidence,
    )
