import json
import importlib.util
from types import SimpleNamespace
from pathlib import Path

import odps_skill.cli as cli
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
