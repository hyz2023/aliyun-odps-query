import json
from types import SimpleNamespace

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
