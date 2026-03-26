import json
import importlib.util
import subprocess
from types import SimpleNamespace
from pathlib import Path

import odps_skill.cli as cli
from odps_skill.client import DependencyMissingError
from odps_skill.cli import build_parser
from odps_skill.cli import main
from odps_skill.schemas import success_response


def test_parser_exposes_expected_subcommands():
    parser = build_parser()
    choices = parser._subparsers._group_actions[0].choices
    assert {"list", "describe", "query", "summarize", "diagnose"} <= set(choices)


def test_success_response_has_stable_top_level_shape():
    result = success_response(action="list", project="demo", data={"items": []})
    assert result["ok"] is True
    assert result["action"] == "list"
    assert "summary" in result
    assert "diagnostics" in result
    assert "meta" in result


def test_cli_defaults_to_json_output(capsys, monkeypatch):
    monkeypatch.setattr(cli, "load_config", lambda **kwargs: SimpleNamespace(project=kwargs["project"]))
    monkeypatch.setattr(
        cli,
        "create_client",
        lambda config: SimpleNamespace(list_tables=lambda: []),
    )
    exit_code = main(["list", "--project", "demo"])
    out = capsys.readouterr().out
    payload = json.loads(out)
    assert exit_code == 0
    assert payload["action"] == "list"


def test_query_command_returns_error_type_for_rejected_sql(capsys):
    exit_code = main(["query", "--project", "demo", "--sql", "DELETE FROM t"])
    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 1
    assert payload["ok"] is False
    assert payload["error"]["type"] == "invalid_query"


def test_legacy_script_entrypoint_delegates_to_new_cli(monkeypatch):
    called = {}

    def fake_main(argv=None):
        called["argv"] = argv
        return 0

    monkeypatch.setattr(cli, "main", fake_main)

    script_path = Path(__file__).resolve().parents[1] / "scripts" / "odps_query.py"
    spec = importlib.util.spec_from_file_location("legacy_odps_query", script_path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)

    module.main(["list", "--project", "demo"])
    assert called["argv"] == ["list", "--project", "demo"]


def test_summarize_command_returns_summary_from_input_json(capsys):
    exit_code = main(
        [
            "summarize",
            "--input-json",
            '{"columns":["id"],"rows":[{"id":1}],"count":1}',
        ]
    )
    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert "returned 1 rows" in payload["summary"].lower()


def test_diagnose_command_returns_diagnostics_from_error_type(capsys):
    exit_code = main(["diagnose", "--error-type", "empty_result"])
    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert any("partition" in item.lower() for item in payload["data"]["diagnostics"])


def test_list_command_maps_missing_dependency_to_structured_error(capsys, monkeypatch):
    monkeypatch.setattr(cli, "load_config", lambda **kwargs: SimpleNamespace(project=kwargs["project"]))
    monkeypatch.setattr(cli, "create_client", lambda config: (_ for _ in ()).throw(DependencyMissingError("pyodps is required")))
    exit_code = main(["list", "--project", "demo"])
    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 1
    assert payload["error"]["type"] == "dependency_missing"


def test_legacy_script_runs_directly_from_repo_root():
    result = subprocess.run(
        ["python", "scripts/odps_query.py", "diagnose", "--error-type", "empty_result", "--output", "json"],
        capture_output=True,
        text=True,
        cwd=Path(__file__).resolve().parents[1],
    )
    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["action"] == "diagnose"
