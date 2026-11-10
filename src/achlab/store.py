"""Persistência do projeto em diretório: `project.json` + `events.jsonl`."""
from __future__ import annotations

import json
import os
from datetime import UTC, datetime
from pathlib import Path

from .model import Project

PROJECT_FILE = "project.json"
EVENTS_FILE = "events.jsonl"


def now_iso() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


def load(path: str | Path) -> Project:
    project_path = Path(path) / PROJECT_FILE
    if not project_path.is_file():
        raise FileNotFoundError(f"projeto não encontrado: {project_path}")
    data = json.loads(project_path.read_text(encoding="utf-8"))
    return Project.from_dict(data)


def save(project: Project, path: str | Path) -> None:
    directory = Path(path)
    directory.mkdir(parents=True, exist_ok=True)
    target = directory / PROJECT_FILE
    tmp = directory / (PROJECT_FILE + ".tmp")
    tmp.write_text(
        json.dumps(project.to_dict(), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    os.replace(tmp, target)


def append_event(
    path: str | Path,
    action: str,
    object_id: str = "",
    detail: str = "",
) -> None:
    directory = Path(path)
    directory.mkdir(parents=True, exist_ok=True)
    event = {
        "ts": now_iso(),
        "action": action,
        "object": object_id,
        "detail": detail,
    }
    with (directory / EVENTS_FILE).open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, ensure_ascii=False) + "\n")


def init_project(path: str | Path, question: str, analyst: str = "") -> Project:
    directory = Path(path)
    if (directory / PROJECT_FILE).exists():
        raise FileExistsError(f"já existe projeto em {directory}")
    project = Project(question=question, analyst=analyst, created_at=now_iso())
    save(project, directory)
    append_event(directory, "init", project.question)
    return project


def next_id(existing: list[str], prefix: str) -> str:
    n = 1
    while f"{prefix}{n}" in existing:
        n += 1
    return f"{prefix}{n}"
