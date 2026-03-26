from typing import Any


def success_response(
    *,
    action: str,
    project: str | None,
    data: Any,
    target: str | None = None,
    summary: str = "",
    diagnostics: list[str] | None = None,
    meta: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "ok": True,
        "action": action,
        "project": project,
        "target": target,
        "data": data,
        "summary": summary,
        "diagnostics": diagnostics or [],
        "meta": meta or {},
    }


def error_response(
    *,
    action: str,
    project: str | None,
    error_type: str,
    message: str,
    target: str | None = None,
    diagnostics: list[str] | None = None,
    meta: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "ok": False,
        "action": action,
        "project": project,
        "target": target,
        "data": None,
        "summary": "Command failed.",
        "diagnostics": diagnostics or [],
        "error": {
            "type": error_type,
            "message": message,
            "retryable": False,
        },
        "meta": meta or {},
    }
