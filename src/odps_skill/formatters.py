import json
from typing import Any


def render(payload: dict[str, Any], output: str = "json") -> str:
    if output == "json":
        return json.dumps(payload, ensure_ascii=False)
    raise ValueError(f"Unsupported output format: {output}")
