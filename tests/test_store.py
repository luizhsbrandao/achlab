import json

import pytest

from achlab import store


def test_init_e_load(tmp_path):
    project = store.init_project(tmp_path, "Pergunta", "dev")
    assert project.question == "Pergunta"
    assert (tmp_path / "project.json").is_file()
    loaded = store.load(tmp_path)
    assert loaded.question == "Pergunta"
    assert loaded.analyst == "dev"
    events = (tmp_path / "events.jsonl").read_text(encoding="utf-8").splitlines()
    assert len(events) == 1
    assert json.loads(events[0])["action"] == "init"


def test_init_existente_falha(tmp_path):
    store.init_project(tmp_path, "Pergunta")
    with pytest.raises(FileExistsError):
        store.init_project(tmp_path, "Outra")


def test_save_estavel(tmp_path):
    project = store.init_project(tmp_path, "Pergunta")
    before = (tmp_path / "project.json").read_bytes()
    store.save(project, tmp_path)
    assert (tmp_path / "project.json").read_bytes() == before


def test_append_event(tmp_path):
    store.init_project(tmp_path, "Pergunta")
    store.append_event(tmp_path, "ev_add", "E1", "detalhe")
    lines = (tmp_path / "events.jsonl").read_text(encoding="utf-8").splitlines()
    assert [json.loads(line)["action"] for line in lines] == ["init", "ev_add"]
    assert json.loads(lines[1])["object"] == "E1"


def test_next_id():
    assert store.next_id(["H1", "H3"], "H") == "H2"
    assert store.next_id([], "E") == "E1"
    assert store.next_id(["H1", "H2"], "H") == "H3"
