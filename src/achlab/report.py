"""Relatório Markdown determinístico."""
from __future__ import annotations

from .model import Project
from .scoring import (
    confidence,
    diagnosticity,
    leave_one_out,
    provenance,
    rank,
    weight,
)


def build(project: Project, allow_incomplete: bool = False) -> str:
    hypothesis_ids = [h.id for h in project.active_hypotheses()]
    accepted = project.accepted_evidence()
    result = rank(project)
    loo = leave_one_out(project)
    prov = provenance(project)
    band, detail = confidence(project, result, loo, prov)

    lines: list[str] = []
    if allow_incomplete and prov < 1.0:
        lines.extend(["> **ANÁLISE INCOMPLETA — NÃO CITÁVEL**", ""])
    lines.append(f"# {project.question}")
    if project.scope:
        lines.extend(["", project.scope])
    if project.classification:
        lines.extend(["", f"Classificação: `{project.classification}`"])

    lines.extend(["", "## Matriz de consistência", ""])
    if accepted:
        lines.append("| Evidência | w | D | " + " | ".join(hypothesis_ids) + " |")
        lines.append("|---|---|---|" + "---|" * len(hypothesis_ids))
        for ev in accepted:
            cells = [ev.consistency(h) for h in hypothesis_ids]
            lines.append(
                f"| {ev.id} | {weight(ev):.3f} | {diagnosticity(ev, hypothesis_ids):.2f} | "
                + " | ".join(cells)
                + " |"
            )
    else:
        lines.append("Nenhuma evidência aceita.")

    lines.extend(["", "## Ranking (menor inconsistência)", ""])
    if result["tie"]:
        lines.append("**EMPATE TÉCNICO — INDETERMINADO.**")
        lines.append("")
    if result["rows"]:
        lines.append("| # | Hipótese | I | S |")
        lines.append("|---|---|---|---|")
        for i, row in enumerate(result["rows"], 1):
            lines.append(f"| {i} | {row['id']} | {row['I']:.3f} | {row['S']:.3f} |")
    else:
        lines.append("Nenhuma hipótese ativa.")

    lines.extend(["", "## Métricas", ""])
    lines.append(f"- Margem absoluta: {result['margin_abs']:.3f}")
    lines.append(f"- Margem relativa: {result['margin_rel']:.3f}")
    lines.append(
        f"- Robustez: {loo['robustness']:.3f} ({loo['preserved']}/{loo['runs']})"
    )
    lines.append(
        f"- Evidências decisivas: {', '.join(loo['decisive']) or 'nenhuma'}"
    )
    lines.append(f"- Proveniência: {prov:.2f}")
    lines.append(f"- Evidências diagnósticas: {detail['diagnostic']}")
    lines.append(f"- Faixa: **{band}**")

    lines.extend(["", "## Fontes", ""])
    if accepted:
        for ev in accepted:
            locator = ev.source.url or ev.source.archive_url or ev.source.locator
            lines.append(f"- **{ev.id}** — {ev.source.citation} — `{locator}`")
    else:
        lines.append("Nenhuma fonte aceita.")

    unused = [e for e in project.evidence if e.status != "aceita"]
    if unused:
        lines.extend(["", "## Evidências não usadas", ""])
        for ev in unused:
            lines.append(f"- **{ev.id}** — {ev.title} (`{ev.status}`)")

    if project.assumptions:
        lines.extend(["", "## Premissas", ""])
        for assumption in project.assumptions:
            statement = assumption.get("statement", "")
            status = assumption.get("status", "não testada")
            lines.append(f"- {statement} (`{status}`)")

    lines.extend(
        [
            "",
            "---",
            "",
            "A faixa avalia a robustez **da análise**, não a probabilidade da hipótese.",
            "O relatório não usa linguagem probabilística e não substitui o julgamento do analista.",
        ]
    )
    return "\n".join(lines) + "\n"
