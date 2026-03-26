import json

from odps_skill.schemas import success_response
from odps_skill.formatters import render


def test_render_json_serializes_payload():
    payload = {"ok": True, "action": "list"}
    rendered = render(payload)
    assert json.loads(rendered) == payload


def test_text_and_table_render_same_underlying_payload():
    payload = success_response(
        action="describe",
        project="demo",
        data={"columns": [{"name": "id", "type": "BIGINT"}], "partitions": []},
    )
    text = render(payload, output="text")
    table = render(payload, output="table")
    assert "id" in text
    assert "id" in table


def test_text_render_includes_error_details():
    payload = {
        "ok": False,
        "action": "describe",
        "summary": "Command failed.",
        "diagnostics": ["Install pyodps before using ODPS-backed commands."],
        "error": {"type": "dependency_missing", "message": "pyodps is required"},
        "data": None,
    }
    text = render(payload, output="text")
    assert "pyodps is required" in text
