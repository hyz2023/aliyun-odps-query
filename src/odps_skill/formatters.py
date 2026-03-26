import json
from typing import Any


def render(payload: dict[str, Any], output: str = "json") -> str:
    if output == "json":
        return json.dumps(payload, ensure_ascii=False)
    if output == "text":
        return render_text(payload)
    if output == "table":
        return render_table(payload)
    raise ValueError(f"Unsupported output format: {output}")


def render_text(payload: dict[str, Any]) -> str:
    lines = [f"Action: {payload['action']}"]
    if payload.get("summary"):
        lines.append(payload["summary"])
    error = payload.get("error") or {}
    if error.get("message"):
        lines.append(f"Error: {error['message']}")
    diagnostics = payload.get("diagnostics") or []
    if diagnostics:
        lines.extend(f"- {item}" for item in diagnostics)
    data = payload.get("data") or {}
    columns = data.get("columns", [])
    if columns:
        lines.append("Columns: " + ", ".join(column["name"] for column in columns))
    return "\n".join(lines)


def render_table(payload: dict[str, Any]) -> str:
    data = payload.get("data") or {}
    columns = data.get("columns", [])
    if columns:
        header = " | ".join(column["name"] for column in columns)
        types = " | ".join(column.get("type", "") for column in columns)
        return "\n".join([header, types])
    return render_text(payload)
