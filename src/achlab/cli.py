"""CLI do achlab."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import store
from .demo import build_demo
from .model import Assessment, Evidence, Hypothesis, Project, Source, validate
from .report import build as build_report
from .scoring import confidence, leave_one_out, provenance, rank


def _add_common(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--dir", default=".", help="diretório do projeto (default: .)")


def _load(args: argparse.Namespace) -> Project:
    return store.load(args.dir)


def _print_errors(errors: list[str]) -> None:
    for error in errors:
        print(f"erro: {error}", file=sys.stderr)


def cmd_init(args: argparse.Namespace) -> int:
    try:
        project = store.init_project(args.dir, args.question, args.analyst)
    except FileExistsError as exc:
        print(f"erro: {exc}", file=sys.stderr)
        return 1
    print(f"projeto criado em {Path(args.dir).resolve()} — {project.question}")
    return 0


def cmd_hyp_add(args: argparse.Namespace) -> int:
    project = _load(args)
    ids = [h.id for h in project.hypotheses]
    hypothesis_id = args.id or store.next_id(ids, "H")
    if hypothesis_id in ids:
        print(f"erro: hipótese {hypothesis_id} já existe", file=sys.stderr)
        return 1
    project.hypotheses.append(
        Hypothesis(
            id=hypothesis_id,
            statement=args.statement,
            definition=args.definition,
        )
    )
    store.save(project, args.dir)
    store.append_event(args.dir, "hyp_add", hypothesis_id, args.statement)
    print(f"{hypothesis_id}: {args.statement}")
    return 0


def cmd_ev_add(args: argparse.Namespace) -> int:
    project = _load(args)
    ids = [e.id for e in project.evidence]
    evidence_id = args.id or store.next_id(ids, "E")
    if evidence_id in ids:
        print(f"erro: evidência {evidence_id} já existe", file=sys.stderr)
        return 1
    source = Source(
        citation=args.source,
        url=args.url or "",
        archive_url=args.archive or "",
        locator=args.locator or "",
    )
    project.evidence.append(
        Evidence(
            id=evidence_id,
            title=args.title,
            source=source,
            reliability=args.reliability,
            credibility=args.credibility,
            relevance=args.relevance,
            excerpt=args.excerpt,
            status="draft",
            date_of_information=args.date or "",
        )
    )
    store.save(project, args.dir)
    store.append_event(args.dir, "ev_add", evidence_id, args.title)
    print(f"{evidence_id}: {args.title} (draft; use `ach ev accept {evidence_id}`)")
    return 0


def cmd_ev_accept(args: argparse.Namespace) -> int:
    project = _load(args)
    evidence = project.evidence_item(args.id)
    if evidence is None:
        print(f"erro: evidência {args.id} não existe", file=sys.stderr)
        return 1
    evidence.status = "aceita"
    errors = validate(project)
    if errors:
        _print_errors(errors)
        return 2
    store.save(project, args.dir)
    store.append_event(args.dir, "ev_accept", evidence.id)
    print(f"{evidence.id}: aceita")
    return 0


def cmd_ev_reject(args: argparse.Namespace) -> int:
    project = _load(args)
    evidence = project.evidence_item(args.id)
    if evidence is None:
        print(f"erro: evidência {args.id} não existe", file=sys.stderr)
        return 1
    evidence.status = "rejeitada"
    store.save(project, args.dir)
    store.append_event(args.dir, "ev_reject", evidence.id, args.reason)
    print(f"{evidence.id}: rejeitada — {args.reason}")
    return 0


def cmd_assess(args: argparse.Namespace) -> int:
    project = _load(args)
    evidence = project.evidence_item(args.evidence)
    hypothesis = project.hypothesis(args.hypothesis)
    if evidence is None:
        print(f"erro: evidência {args.evidence} não existe", file=sys.stderr)
        return 1
    if hypothesis is None:
        print(f"erro: hipótese {args.hypothesis} não existe", file=sys.stderr)
        return 1
    if hypothesis.status != "ativa":
        print(f"erro: hipótese {hypothesis.id} não está ativa", file=sys.stderr)
        return 1
    evidence.assessments[hypothesis.id] = Assessment(
        consistency=args.consistency,
        rationale=args.rationale,
        author=args.author or project.analyst,
        ts=store.now_iso(),
    )
    store.save(project, args.dir)
    store.append_event(
        args.dir,
        "assess",
        f"{evidence.id}/{hypothesis.id}",
        args.consistency,
    )
    print(f"{evidence.id} × {hypothesis.id}: {args.consistency}")
    return 0


def cmd_score(args: argparse.Namespace) -> int:
    project = _load(args)
    errors = validate(project)
    if errors:
        _print_errors(errors)
        return 2
    result = rank(project)
    loo = leave_one_out(project)
    prov = provenance(project)
    band, detail = confidence(project, result, loo, prov)

    if args.json:
        payload = {
            "ranking": result,
            "leave_one_out": loo,
            "provenance": prov,
            "confidence": band,
            "detail": detail,
        }
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0

    if result["tie"]:
        print("EMPATE TÉCNICO — INDETERMINADO")
    print("Ranking (menor inconsistência)")
    for i, row in enumerate(result["rows"], 1):
        print(f"{i}. {row['id']}  I={row['I']:.3f}  S={row['S']:.3f}")
    print(
        f"Margem: abs {result['margin_abs']:.3f} · rel {result['margin_rel']:.3f}"
    )
    print(
        f"Robustez: {loo['robustness']:.3f} ({loo['preserved']}/{loo['runs']}); "
        f"decisivas: {', '.join(loo['decisive']) or 'nenhuma'}"
    )
    print(f"Proveniência: {prov:.2f}")
    print(f"Faixa: {band}")
    return 0


def cmd_report(args: argparse.Namespace) -> int:
    project = _load(args)
    errors = validate(project)
    if errors:
        _print_errors(errors)
        return 2
    prov = provenance(project)
    if prov < 1.0 and not args.allow_incomplete:
        print(
            "erro: proveniência incompleta; gere com --allow-incomplete para "
            "obter o carimbo NÃO CITÁVEL",
            file=sys.stderr,
        )
        return 3
    markdown = build_report(project, allow_incomplete=args.allow_incomplete)
    if args.md:
        target = Path(args.md)
        target.write_text(markdown, encoding="utf-8")
        print(target)
    else:
        print(markdown, end="")
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    project = _load(args)
    errors = validate(project)
    if errors:
        _print_errors(errors)
        return 2
    active = len(project.active_hypotheses())
    accepted = len(project.accepted_evidence())
    print(
        f"ok: {active} hipótese{'s' if active != 1 else ''} ativa{'s' if active != 1 else ''}, "
        f"{accepted} evidência{'s' if accepted != 1 else ''} aceita{'s' if accepted != 1 else ''}"
    )
    return 0


def cmd_demo(args: argparse.Namespace) -> int:
    project = build_demo()
    if args.write:
        store.save(project, args.write)
        store.append_event(args.write, "demo", project.question)
        print(f"demo gravada em {Path(args.write).resolve()}")
    print(build_report(project), end="")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ach",
        description="Analysis of Competing Hypotheses com proveniência auditável.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_init = sub.add_parser("init", help="cria um projeto")
    p_init.add_argument("question")
    p_init.add_argument("--analyst", default="")
    _add_common(p_init)
    p_init.set_defaults(func=cmd_init)

    p_hyp = sub.add_parser("hyp", help="gerencia hipóteses")
    hyp_sub = p_hyp.add_subparsers(dest="hyp_command", required=True)
    p_hyp_add = hyp_sub.add_parser("add", help="adiciona hipótese")
    p_hyp_add.add_argument("statement")
    p_hyp_add.add_argument("--id")
    p_hyp_add.add_argument("--definition", default="")
    _add_common(p_hyp_add)
    p_hyp_add.set_defaults(func=cmd_hyp_add)

    p_ev = sub.add_parser("ev", help="gerencia evidências")
    ev_sub = p_ev.add_subparsers(dest="ev_command", required=True)
    p_ev_add = ev_sub.add_parser("add", help="adiciona evidência (draft)")
    p_ev_add.add_argument("--title", required=True)
    p_ev_add.add_argument("--source", required=True, help="citação da fonte")
    p_ev_add.add_argument("--reliability", required=True, choices=list("ABCDEF"))
    p_ev_add.add_argument("--credibility", required=True, type=int, choices=range(1, 7))
    p_ev_add.add_argument("--relevance", required=True, choices=["alta", "media", "baixa"])
    p_ev_add.add_argument("--excerpt", required=True)
    p_ev_add.add_argument("--url", default="")
    p_ev_add.add_argument("--archive", default="")
    p_ev_add.add_argument("--locator", default="")
    p_ev_add.add_argument("--date", default="")
    p_ev_add.add_argument("--id")
    _add_common(p_ev_add)
    p_ev_add.set_defaults(func=cmd_ev_add)

    p_ev_accept = ev_sub.add_parser("accept", help="aceita evidência")
    p_ev_accept.add_argument("id")
    _add_common(p_ev_accept)
    p_ev_accept.set_defaults(func=cmd_ev_accept)

    p_ev_reject = ev_sub.add_parser("reject", help="rejeita evidência")
    p_ev_reject.add_argument("id")
    p_ev_reject.add_argument("--reason", required=True)
    _add_common(p_ev_reject)
    p_ev_reject.set_defaults(func=cmd_ev_reject)

    p_assess = sub.add_parser("assess", help="avalia evidência × hipótese")
    p_assess.add_argument("evidence")
    p_assess.add_argument("hypothesis")
    p_assess.add_argument("--consistency", required=True, choices=["++", "+", "0", "-", "--", "na"])
    p_assess.add_argument("--rationale", required=True)
    p_assess.add_argument("--author", default="")
    _add_common(p_assess)
    p_assess.set_defaults(func=cmd_assess)

    p_score = sub.add_parser("score", help="calcula ranking e faixa")
    p_score.add_argument("--json", action="store_true")
    _add_common(p_score)
    p_score.set_defaults(func=cmd_score)

    p_report = sub.add_parser("report", help="gera relatório Markdown")
    p_report.add_argument("--md", default="")
    p_report.add_argument("--allow-incomplete", action="store_true")
    _add_common(p_report)
    p_report.set_defaults(func=cmd_report)

    p_validate = sub.add_parser("validate", help="valida integridade do projeto")
    _add_common(p_validate)
    p_validate.set_defaults(func=cmd_validate)

    p_demo = sub.add_parser("demo", help="roda o caso sintético")
    p_demo.add_argument("--write", default="")
    p_demo.set_defaults(func=cmd_demo)

    return parser


def _normalize_argv(argv: list[str] | None) -> list[str] | None:
    """Permite `--consistency --` (argparse trataria `--` como fim das opções)."""
    if argv is None:
        return None
    normalized: list[str] = []
    i = 0
    while i < len(argv):
        if argv[i] == "--consistency" and i + 1 < len(argv):
            normalized.append(f"--consistency={argv[i + 1]}")
            i += 2
            continue
        normalized.append(argv[i])
        i += 1
    return normalized


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    raw = sys.argv[1:] if argv is None else argv
    args = parser.parse_args(_normalize_argv(raw))
    try:
        return args.func(args)
    except FileNotFoundError as exc:
        print(f"erro: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
