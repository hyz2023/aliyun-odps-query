from odps_skill.cli import build_parser
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
