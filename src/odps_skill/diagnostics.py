def build_summary(*, action: str, data: dict, meta: dict | None = None) -> str:
    meta = meta or {}
    if action == "query":
        base = f"Returned {data.get('count', 0)} rows across {len(data.get('columns', []))} columns."
        if meta.get("truncated"):
            return f"{base} Result set was truncated."
        return base
    if action == "list":
        return f"Found {data.get('count', 0)} matching tables."
    if action == "describe":
        return (
            f"Table has {len(data.get('columns', []))} columns and "
            f"{len(data.get('partitions', []))} partitions."
        )
    return ""


def build_diagnostics(*, error_type: str | None = None, context: dict | None = None) -> list[str]:
    if error_type == "empty_result":
        return [
            "Check partition filters and date predicates.",
            "Relax overly strict WHERE conditions and rerun the query.",
        ]
    if error_type == "invalid_query":
        return ["Only read-only SELECT-style SQL is supported by this local skill."]
    if error_type == "dependency_missing":
        return ["Install pyodps before using ODPS-backed commands."]
    return []
