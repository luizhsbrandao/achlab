"""Servidor MCP somente-leitura do achlab.

Compatível com `mcp` 1.x (FastMCP) e 2.x (MCPServer). Todas as ferramentas são de leitura:
o analista escreve pela CLI, não por um agente.
"""
from __future__ import annotations

import argparse
import os
from pathlib import Path

try:  # mcp >= 2
    from mcp.server.mcpserver import MCPServer
except ImportError:  # mcp 1.x
    from mcp.server.fastmcp import FastMCP as MCPServer  # type: ignore[assignment]

from . import store
from .report import build as build_report
from .scoring import evaluate, provenance

ROOT = Path.cwd().resolve()
MAX_DEPTH = 4


def configure(root: str | Path) -> None:
    global ROOT
    ROOT = Path(root).resolve()


def _within_root(path: Path) -> bool:
    """True se o caminho resolvido (symlinks incluídos) está sob ROOT."""
    resolved = path.resolve()
    return resolved == ROOT or ROOT in resolved.parents


def _resolve(project: str) -> Path:
    candidate = Path(project)
    if not candidate.is_absolute():
        candidate = ROOT / candidate
    candidate = candidate.resolve()
    if not _within_root(candidate):
        raise ValueError("projeto fora da raiz permitida")
    project_file = candidate / store.PROJECT_FILE
    if not project_file.is_file():
        raise FileNotFoundError(f"projeto não encontrado: {candidate}")
    if not _within_root(project_file):
        raise ValueError("project.json fora da raiz permitida")
    return candidate


def _project(project: str):
    return store.load(_resolve(project))


server = MCPServer("achlab", description="Read-only ACH analysis with auditable provenance.")


@server.tool(name="ach_list_projects", description="Lista projetos ACH sob a raiz configurada.")
def ach_list_projects() -> list[dict]:
    found: list[dict] = []
    base_depth = len(ROOT.parts)
    for current, dirs, files in os.walk(ROOT):
        dirs[:] = [
            d for d in dirs if not d.startswith(".") and d not in {"build", "dist", "__pycache__"}
        ]
        if store.PROJECT_FILE not in files:
            if len(Path(current).parts) - base_depth >= MAX_DEPTH:
                dirs[:] = []
            continue
        project_file = Path(current) / store.PROJECT_FILE
        if not _within_root(project_file):
            continue
        try:
            project = store.load(current)
        except Exception:
            continue
        found.append(
            {
                "path": str(Path(current).relative_to(ROOT)),
                "question": project.question,
                "hypotheses": len(project.active_hypotheses()),
                "evidence": len(project.accepted_evidence()),
            }
        )
        dirs[:] = []
    return sorted(found, key=lambda item: item["path"])


@server.tool(name="ach_get_project", description="Lê um projeto ACH (JSON do projeto).")
def ach_get_project(project: str) -> dict:
    return _project(project).to_dict()


@server.tool(name="ach_score", description="Calcula ranking, margem, robustez e faixa.")
def ach_score(project: str) -> dict:
    data = _project(project)
    evaluation = evaluate(data)
    return {
        "question": data.question,
        "ranking": evaluation["ranking"],
        "leave_one_out": evaluation["leave_one_out"],
        "provenance": evaluation["provenance"],
        "confidence": evaluation["confidence"],
        "detail": evaluation["detail"],
    }


@server.tool(name="ach_report", description="Gera o relatório Markdown; recusa proveniência incompleta.")
def ach_report(project: str) -> str:
    data = _project(project)
    if provenance(data) < 1.0:
        raise ValueError("proveniência incompleta; o relatório seria NÃO CITÁVEL")
    return build_report(data)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="ach-mcp", description="Servidor MCP do achlab")
    parser.add_argument("--root", default=".", help="raiz permitida para leitura")
    args = parser.parse_args(argv)
    configure(args.root)
    server.run()


if __name__ == "__main__":
    main()
