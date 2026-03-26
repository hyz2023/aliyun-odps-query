import json

from odps_skill.formatters import render


def test_render_json_serializes_payload():
    payload = {"ok": True, "action": "list"}
    rendered = render(payload)
    assert json.loads(rendered) == payload
