import json

from achlab import store
from achlab.cli import main


def run(*args):
    return main(list(args))


def init_case(tmp_path, with_locator=True):
    directory = str(tmp_path / "p")
    assert run("init", "Caso", "--dir", directory, "--analyst", "dev") == 0
    assert run("hyp", "add", "H1: insider", "--dir", directory) == 0
    assert run("hyp", "add", "H2: externo", "--dir", directory) == 0
    args = [
        "ev",
        "add",
        "--title",
        "Log",
        "--source",
        "Log sintético",
        "--reliability",
        "A",
        "--credibility",
        "1",
        "--relevance",
        "alta",
        "--excerpt",
        "Acesso às 22h",
        "--dir",
        directory,
    ]
    if with_locator:
        args += ["--locator", "fixture://log"]
    assert run(*args) == 0
    return directory


def test_cli_ponta_a_ponta(tmp_path, capsys):
    directory = init_case(tmp_path)
    assert run("assess", "E1", "H1", "--consistency", "++", "--rationale", "ok", "--dir", directory) == 0
    assert run("assess", "E1", "H2", "--consistency", "--", "--rationale", "não", "--dir", directory) == 0

    assert run("report", "--dir", directory) == 3
    assert run("ev", "accept", "E1", "--dir", directory) == 0
    assert run("score", "--dir", directory) == 0
    output = capsys.readouterr().out
    assert "H1" in output
    assert "Faixa:" in output

    report_path = tmp_path / "report.md"
    assert run("report", "--dir", directory, "--md", str(report_path)) == 0
    assert report_path.is_file()
    assert "# Caso" in report_path.read_text(encoding="utf-8")


def test_consistencia_duplo_traco(tmp_path):
    directory = init_case(tmp_path)
    assert run(
        "assess", "E1", "H1", "--consistency", "--", "--rationale", "r", "--dir", directory
    ) == 0
    project = store.load(directory)
    assert project.evidence[0].assessments["H1"].consistency == "--"


def test_validate_sem_justificativa(tmp_path, capsys):
    directory = init_case(tmp_path)
    assert run(
        "assess", "E1", "H1", "--consistency", "++", "--rationale", "", "--dir", directory
    ) == 0
    assert run("validate", "--dir", directory) == 2
    assert "justificativa" in capsys.readouterr().err


def test_accept_sem_localizador(tmp_path, capsys):
    directory = init_case(tmp_path, with_locator=False)
    assert run("ev", "accept", "E1", "--dir", directory) == 2
    assert "sem localizador" in capsys.readouterr().err


def test_report_incompleto(tmp_path, capsys):
    directory = init_case(tmp_path)
    assert run("report", "--dir", directory) == 3
    assert run("report", "--dir", directory, "--allow-incomplete") == 0
    assert "NÃO CITÁVEL" in capsys.readouterr().out


def test_demo(capsys):
    assert run("demo") == 0
    output = capsys.readouterr().out
    assert "Faixa: **MODERADA**" in output
    assert "H1" in output


def test_score_json(tmp_path, capsys):
    directory = str(tmp_path / "demo")
    assert run("demo", "--write", directory) == 0
    capsys.readouterr()
    assert run("score", "--dir", directory, "--json") == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["confidence"] == "MODERADA"
    assert payload["ranking"]["rows"][0]["id"] == "H1"


def test_validar_demo(tmp_path, capsys):
    directory = str(tmp_path / "demo")
    assert run("demo", "--write", directory) == 0
    capsys.readouterr()
    assert run("validate", "--dir", directory) == 0
    assert "ok:" in capsys.readouterr().out


def test_projeto_ausente(tmp_path, capsys):
    assert run("validate", "--dir", str(tmp_path / "nope")) == 1
    assert "projeto não encontrado" in capsys.readouterr().err


def test_init_existente(tmp_path, capsys):
    directory = str(tmp_path / "p")
    assert run("init", "Caso", "--dir", directory) == 0
    assert run("init", "Caso", "--dir", directory) == 1
    assert "já existe" in capsys.readouterr().err


def test_ids_inexistentes(tmp_path, capsys):
    directory = init_case(tmp_path)
    assert run("assess", "E9", "H1", "--consistency", "+", "--rationale", "r", "--dir", directory) == 1
    assert run("assess", "E1", "H9", "--consistency", "+", "--rationale", "r", "--dir", directory) == 1
    assert "não existe" in capsys.readouterr().err


def test_hyp_duplicada(tmp_path, capsys):
    directory = init_case(tmp_path)
    assert run("hyp", "add", "H1 de novo", "--id", "H1", "--dir", directory) == 1
    assert "já existe" in capsys.readouterr().err
