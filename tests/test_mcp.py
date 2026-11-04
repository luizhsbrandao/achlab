import pytest

pytest.importorskip("mcp")

from achlab import mcp_server, store
from achlab.demo import build_demo


@pytest.fixture
def root(tmp_path):
    mcp_server.configure(tmp_path)
    directory = tmp_path / "case"
    store.save(build_demo(), directory)
    return tmp_path


def test_lista_projetos(root):
    found = mcp_server.ach_list_projects()
    assert [item["path"] for item in found] == ["case"]
    assert found[0]["hypotheses"] == 3


def test_le_projeto(root):
    data = mcp_server.ach_get_project("case")
    assert data["question"].startswith("Quem divulgou")


def test_score(root):
    payload = mcp_server.ach_score("case")
    assert payload["confidence"] == "MODERADA"
    assert payload["ranking"]["rows"][0]["id"] == "H1"


def test_report(root):
    markdown = mcp_server.ach_report("case")
    assert "# Quem divulgou" in markdown
    assert "Faixa: **MODERADA**" in markdown


def test_recusa_fora_da_raiz(root):
    with pytest.raises(ValueError):
        mcp_server.ach_get_project("../fora")


def test_projeto_ausente(root):
    with pytest.raises(FileNotFoundError):
        mcp_server.ach_get_project("nao-existe")


def test_report_recusa_proveniencia_incompleta(root):
    project = mcp_server._project("case")
    project.evidence[0].status = "draft"
    store.save(project, root / "case")
    with pytest.raises(ValueError):
        mcp_server.ach_report("case")
