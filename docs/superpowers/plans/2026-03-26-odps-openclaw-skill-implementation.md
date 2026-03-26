# ODPS OpenClaw Skill Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Refactor the current local ODPS query script into a JSON-first, OpenClaw-friendly local skill with read-only guardrails, summaries, diagnostics, and stable CLI contracts.

**Architecture:** Keep the external interface CLI-first while moving the implementation into a small package under `src/odps_skill/`. Normalize every command through one response envelope, then render that envelope through formatters for `json`, `text`, and `table`. Preserve the current script path as a compatibility shim so existing local usage does not break during the refactor.

**Tech Stack:** Python 3, `pyodps`, `pandas`, `pytest`, `argparse`, standard library dataclasses or typed dicts, editable package entrypoint via `pyproject.toml`

---

## File Map

### New files

- `pyproject.toml`: package metadata and console-script entrypoint
- `src/odps_skill/__init__.py`: package marker
- `src/odps_skill/cli.py`: argument parsing and command routing
- `src/odps_skill/config.py`: runtime config loading and validation
- `src/odps_skill/client.py`: ODPS client creation
- `src/odps_skill/schemas.py`: normalized response envelope helpers
- `src/odps_skill/metadata.py`: `list` and `describe` operations
- `src/odps_skill/query.py`: read-only SQL guardrails and query execution
- `src/odps_skill/diagnostics.py`: summaries and deterministic diagnostics
- `src/odps_skill/formatters.py`: `json`, `text`, and `table` rendering
- `tests/test_cli.py`: CLI contract tests
- `tests/test_config.py`: config validation tests
- `tests/test_metadata.py`: metadata normalization tests
- `tests/test_query_guardrails.py`: read-only SQL tests
- `tests/test_formatters.py`: formatter contract tests
- `tests/test_diagnostics.py`: summary and diagnostics tests

### Modified files

- `scripts/odps_query.py`: turn into a compatibility shim that calls the new CLI
- `SKILL.md`: rewrite as an OpenClaw-facing local skill protocol
- `README.md`: align with the new JSON-first CLI contract

## Chunk 1: Package Skeleton and Response Contract

### Task 1: Create package scaffolding and CLI entrypoint

**Files:**
- Create: `pyproject.toml`
- Create: `src/odps_skill/__init__.py`
- Create: `src/odps_skill/cli.py`
- Test: `tests/test_cli.py`

- [ ] **Step 1: Write the failing CLI entrypoint tests**

```python
from odps_skill.cli import build_parser


def test_parser_exposes_expected_subcommands():
    parser = build_parser()
    choices = parser._subparsers._group_actions[0].choices
    assert {"list", "describe", "query", "summarize", "diagnose"} <= set(choices)
```

- [ ] **Step 2: Run the parser test to verify it fails**

Run: `pytest tests/test_cli.py::test_parser_exposes_expected_subcommands -v`
Expected: FAIL with `ModuleNotFoundError` or missing `build_parser`

- [ ] **Step 3: Add the package scaffold and minimal parser implementation**

```python
def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="odps-skill")
    subparsers = parser.add_subparsers(dest="command", required=True)
    for name in ("list", "describe", "query", "summarize", "diagnose"):
        subparsers.add_parser(name)
    return parser
```

- [ ] **Step 4: Add `pyproject.toml` with an editable console script**

```toml
[project.scripts]
odps-skill = "odps_skill.cli:main"
```

- [ ] **Step 5: Run the parser test to verify it passes**

Run: `pytest tests/test_cli.py::test_parser_exposes_expected_subcommands -v`
Expected: PASS

- [ ] **Step 6: Commit the scaffold**

```bash
git add pyproject.toml src/odps_skill/__init__.py src/odps_skill/cli.py tests/test_cli.py
git commit -m "feat: scaffold odps skill package"
```

### Task 2: Define the normalized response envelope

**Files:**
- Create: `src/odps_skill/schemas.py`
- Modify: `src/odps_skill/cli.py`
- Test: `tests/test_cli.py`

- [ ] **Step 1: Write a failing response-envelope test**

```python
from odps_skill.schemas import success_response


def test_success_response_has_stable_top_level_shape():
    result = success_response(action="list", project="demo", data={"items": []})
    assert result["ok"] is True
    assert result["action"] == "list"
    assert "summary" in result
    assert "diagnostics" in result
    assert "meta" in result
```

- [ ] **Step 2: Run the envelope test to verify it fails**

Run: `pytest tests/test_cli.py::test_success_response_has_stable_top_level_shape -v`
Expected: FAIL with missing schema helper

- [ ] **Step 3: Implement success/error envelope helpers**

```python
def success_response(*, action, project, data, target=None, summary="", diagnostics=None, meta=None):
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
```

- [ ] **Step 4: Wire `cli.py` to return this envelope from temporary command handlers**

```python
return success_response(action=args.command, project=args.project, data={})
```

- [ ] **Step 5: Run the envelope test to verify it passes**

Run: `pytest tests/test_cli.py::test_success_response_has_stable_top_level_shape -v`
Expected: PASS

- [ ] **Step 6: Commit the schema layer**

```bash
git add src/odps_skill/schemas.py src/odps_skill/cli.py tests/test_cli.py
git commit -m "feat: add normalized response envelope"
```

### Task 3: Add JSON output as the default CLI contract

**Files:**
- Modify: `src/odps_skill/cli.py`
- Create: `src/odps_skill/formatters.py`
- Test: `tests/test_cli.py`
- Test: `tests/test_formatters.py`

- [ ] **Step 1: Write a failing test for default JSON output**

```python
def test_cli_defaults_to_json_output(capsys):
    exit_code = main(["list", "--project", "demo"])
    out = capsys.readouterr().out
    payload = json.loads(out)
    assert exit_code == 0
    assert payload["action"] == "list"
```

- [ ] **Step 2: Run the JSON output test to verify it fails**

Run: `pytest tests/test_cli.py::test_cli_defaults_to_json_output -v`
Expected: FAIL because output is missing or not valid JSON

- [ ] **Step 3: Implement `formatters.py` with `json` rendering and make it the default**

```python
def render(payload, output="json"):
    if output == "json":
        return json.dumps(payload, ensure_ascii=False)
    raise ValueError(f"Unsupported output format: {output}")
```

- [ ] **Step 4: Add `--output` handling to `cli.py` and print rendered payloads**

```python
parser.add_argument("--output", choices=["json", "text", "table"], default="json")
```

- [ ] **Step 5: Run the CLI and formatter tests**

Run: `pytest tests/test_cli.py::test_cli_defaults_to_json_output tests/test_formatters.py -v`
Expected: PASS

- [ ] **Step 6: Commit JSON-first output support**

```bash
git add src/odps_skill/cli.py src/odps_skill/formatters.py tests/test_cli.py tests/test_formatters.py
git commit -m "feat: make json the default cli output"
```

## Chunk 2: Config, Client, and Metadata Commands

### Task 4: Add config validation and dependency-aware client creation

**Files:**
- Create: `src/odps_skill/config.py`
- Create: `src/odps_skill/client.py`
- Test: `tests/test_config.py`

- [ ] **Step 1: Write failing config validation tests**

```python
def test_load_config_requires_project(monkeypatch):
    monkeypatch.delenv("ALIBABA_ODPS_PROJECT", raising=False)
    with pytest.raises(ValueError, match="project"):
        load_config(project=None)
```

- [ ] **Step 2: Run the config tests to verify they fail**

Run: `pytest tests/test_config.py -v`
Expected: FAIL with missing `load_config`

- [ ] **Step 3: Implement config loading from flags and environment variables**

```python
def load_config(*, access_id=None, access_key=None, endpoint=None, project=None):
    resolved_project = project or os.getenv("ALIBABA_ODPS_PROJECT")
    if not resolved_project:
        raise ValueError("Missing project")
    return RuntimeConfig(...)
```

- [ ] **Step 4: Implement client factory with dependency-aware error mapping**

```python
def create_client(config):
    try:
        from odps import ODPS
    except ImportError as exc:
        raise DependencyMissingError("pyodps is required") from exc
    return ODPS(...)
```

- [ ] **Step 5: Run the config tests to verify they pass**

Run: `pytest tests/test_config.py -v`
Expected: PASS

- [ ] **Step 6: Commit config and client setup**

```bash
git add src/odps_skill/config.py src/odps_skill/client.py tests/test_config.py
git commit -m "feat: add config validation and client factory"
```

### Task 5: Implement the `list` command with normalized metadata payloads

**Files:**
- Create: `src/odps_skill/metadata.py`
- Modify: `src/odps_skill/cli.py`
- Test: `tests/test_metadata.py`
- Test: `tests/test_cli.py`

- [ ] **Step 1: Write failing tests for normalized table-list responses**

```python
def test_list_tables_returns_items_sorted_by_name():
    service = MetadataService(client=FakeClient([...]))
    payload = service.list_tables(project="demo")
    assert payload["items"][0]["name"] == "a_table"
```

- [ ] **Step 2: Run the metadata tests to verify they fail**

Run: `pytest tests/test_metadata.py::test_list_tables_returns_items_sorted_by_name -v`
Expected: FAIL with missing `MetadataService`

- [ ] **Step 3: Implement `list_tables` normalization in `metadata.py`**

```python
def list_tables(self, *, pattern=None):
    items = [...]
    return {"items": sorted(items, key=lambda item: item["name"]), "count": len(items)}
```

- [ ] **Step 4: Route the CLI `list` command through the metadata service**

```python
if args.command == "list":
    data = metadata_service.list_tables(pattern=args.pattern)
```

- [ ] **Step 5: Run the metadata and CLI list tests**

Run: `pytest tests/test_metadata.py tests/test_cli.py::test_cli_defaults_to_json_output -v`
Expected: PASS

- [ ] **Step 6: Commit the `list` command**

```bash
git add src/odps_skill/metadata.py src/odps_skill/cli.py tests/test_metadata.py tests/test_cli.py
git commit -m "feat: add list command metadata service"
```

### Task 6: Implement the `describe` command with schema and partition payloads

**Files:**
- Modify: `src/odps_skill/metadata.py`
- Modify: `src/odps_skill/cli.py`
- Test: `tests/test_metadata.py`
- Test: `tests/test_cli.py`

- [ ] **Step 1: Write a failing test for describe payload structure**

```python
def test_describe_table_returns_columns_and_partitions():
    service = MetadataService(client=FakeClient.with_table_schema())
    payload = service.describe_table("orders")
    assert payload["columns"][0]["name"] == "order_id"
    assert payload["partitions"][0]["name"] == "dt"
```

- [ ] **Step 2: Run the describe test to verify it fails**

Run: `pytest tests/test_metadata.py::test_describe_table_returns_columns_and_partitions -v`
Expected: FAIL with missing `describe_table`

- [ ] **Step 3: Implement schema normalization in `metadata.py`**

```python
def describe_table(self, table_name):
    return {
        "name": table.name,
        "columns": [...],
        "partitions": [...],
        "is_virtual_view": ...,
    }
```

- [ ] **Step 4: Add CLI argument validation for `describe --table`**

```python
if args.command == "describe" and not args.table:
    return emit_error("describe requires --table")
```

- [ ] **Step 5: Run metadata tests**

Run: `pytest tests/test_metadata.py -v`
Expected: PASS

- [ ] **Step 6: Commit the `describe` command**

```bash
git add src/odps_skill/metadata.py src/odps_skill/cli.py tests/test_metadata.py tests/test_cli.py
git commit -m "feat: add describe command schema output"
```

## Chunk 3: Query Guardrails, Errors, Summaries, and Diagnostics

### Task 7: Add read-only SQL validation and mutation blocking

**Files:**
- Create: `src/odps_skill/query.py`
- Test: `tests/test_query_guardrails.py`

- [ ] **Step 1: Write failing guardrail tests**

```python
@pytest.mark.parametrize("sql", [
    "INSERT INTO t SELECT * FROM s",
    "DELETE FROM t WHERE id = 1",
    "DROP TABLE t",
    "SELECT * FROM t; DELETE FROM t",
])
def test_validate_read_only_sql_rejects_mutations(sql):
    with pytest.raises(InvalidQueryError):
        validate_read_only_sql(sql)
```

- [ ] **Step 2: Run the guardrail tests to verify they fail**

Run: `pytest tests/test_query_guardrails.py -v`
Expected: FAIL with missing validator

- [ ] **Step 3: Implement the validator in `query.py`**

```python
MUTATION_KEYWORDS = {"INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "TRUNCATE", "CREATE"}


def validate_read_only_sql(sql: str) -> None:
    normalized = sql.strip().upper()
    if ";" in normalized.rstrip(";"):
        raise InvalidQueryError("Multi-statement SQL is not supported")
    if any(keyword in normalized for keyword in MUTATION_KEYWORDS):
        raise InvalidQueryError("Only read-only SQL is supported")
```

- [ ] **Step 4: Run the guardrail tests to verify they pass**

Run: `pytest tests/test_query_guardrails.py -v`
Expected: PASS

- [ ] **Step 5: Commit the guardrails**

```bash
git add src/odps_skill/query.py tests/test_query_guardrails.py
git commit -m "feat: add read only sql guardrails"
```

### Task 8: Implement query execution, stable error mapping, and diagnostics hooks

**Files:**
- Modify: `src/odps_skill/query.py`
- Modify: `src/odps_skill/schemas.py`
- Modify: `src/odps_skill/cli.py`
- Test: `tests/test_query_guardrails.py`
- Test: `tests/test_cli.py`

- [ ] **Step 1: Write failing tests for query result envelopes and error mapping**

```python
def test_query_command_returns_error_type_for_rejected_sql(capsys):
    exit_code = main(["query", "--project", "demo", "--sql", "DELETE FROM t"])
    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 1
    assert payload["ok"] is False
    assert payload["error"]["type"] == "invalid_query"
```

- [ ] **Step 2: Run the query envelope tests to verify they fail**

Run: `pytest tests/test_query_guardrails.py tests/test_cli.py::test_query_command_returns_error_type_for_rejected_sql -v`
Expected: FAIL

- [ ] **Step 3: Implement query execution and stable error mapping**

```python
def execute_query(...):
    validate_read_only_sql(sql)
    try:
        instance = client.execute_sql(sql, project=project)
    except Exception as exc:
        raise map_query_error(exc) from exc
```

- [ ] **Step 4: Return non-zero exit codes for failed commands and normalized error envelopes**

```python
return error_response(
    action="query",
    project=args.project,
    error_type="invalid_query",
    message=str(exc),
    diagnostics=[...],
)
```

- [ ] **Step 5: Run query and CLI tests**

Run: `pytest tests/test_query_guardrails.py tests/test_cli.py -v`
Expected: PASS

- [ ] **Step 6: Commit query execution and error mapping**

```bash
git add src/odps_skill/query.py src/odps_skill/schemas.py src/odps_skill/cli.py tests/test_query_guardrails.py tests/test_cli.py
git commit -m "feat: add query execution and error mapping"
```

### Task 9: Add summaries and deterministic diagnostics

**Files:**
- Create: `src/odps_skill/diagnostics.py`
- Modify: `src/odps_skill/cli.py`
- Test: `tests/test_diagnostics.py`
- Test: `tests/test_cli.py`

- [ ] **Step 1: Write failing tests for summary and diagnostics rules**

```python
def test_build_query_summary_marks_truncated_results():
    summary = build_summary(action="query", data={"columns": ["id"], "rows": [{"id": 1}], "count": 1}, meta={"truncated": True})
    assert "truncated" in summary.lower()


def test_build_diagnostics_for_empty_result_suggests_partition_checks():
    diagnostics = build_diagnostics(error_type="empty_result", context={"action": "query"})
    assert any("partition" in item.lower() for item in diagnostics)
```

- [ ] **Step 2: Run diagnostics tests to verify they fail**

Run: `pytest tests/test_diagnostics.py -v`
Expected: FAIL with missing helpers

- [ ] **Step 3: Implement rule-based summaries and diagnostics**

```python
def build_summary(*, action, data, meta):
    if action == "query":
        return f"Returned {data['count']} rows across {len(data['columns'])} columns."
```

- [ ] **Step 4: Attach summary and diagnostics generation in CLI handlers**

```python
payload["summary"] = build_summary(...)
payload["diagnostics"] = build_diagnostics(...)
```

- [ ] **Step 5: Run diagnostics and CLI tests**

Run: `pytest tests/test_diagnostics.py tests/test_cli.py -v`
Expected: PASS

- [ ] **Step 6: Commit summaries and diagnostics**

```bash
git add src/odps_skill/diagnostics.py src/odps_skill/cli.py tests/test_diagnostics.py tests/test_cli.py
git commit -m "feat: add summaries and diagnostics"
```

## Chunk 4: Formatter Parity, Compatibility Shim, and Documentation

### Task 10: Finish `text` and `table` renderers from the normalized envelope

**Files:**
- Modify: `src/odps_skill/formatters.py`
- Test: `tests/test_formatters.py`

- [ ] **Step 1: Write failing formatter parity tests**

```python
def test_text_and_table_render_same_underlying_payload():
    payload = success_response(action="describe", project="demo", data={"columns": [{"name": "id", "type": "BIGINT"}]})
    text = render(payload, output="text")
    table = render(payload, output="table")
    assert "id" in text
    assert "id" in table
```

- [ ] **Step 2: Run formatter tests to verify they fail**

Run: `pytest tests/test_formatters.py -v`
Expected: FAIL with unsupported formatter branches

- [ ] **Step 3: Implement concise `text` and terminal-friendly `table` output**

```python
if output == "text":
    return render_text(payload)
if output == "table":
    return render_table(payload)
```

- [ ] **Step 4: Run formatter tests**

Run: `pytest tests/test_formatters.py -v`
Expected: PASS

- [ ] **Step 5: Commit formatter parity**

```bash
git add src/odps_skill/formatters.py tests/test_formatters.py
git commit -m "feat: add text and table renderers"
```

### Task 11: Convert the legacy script into a compatibility shim

**Files:**
- Modify: `scripts/odps_query.py`
- Test: `tests/test_cli.py`

- [ ] **Step 1: Write a failing compatibility test**

```python
def test_legacy_script_entrypoint_delegates_to_new_cli(monkeypatch):
    called = {}
    monkeypatch.setattr("odps_skill.cli.main", lambda argv=None: called.setdefault("argv", argv) or 0)
    import scripts.odps_query as legacy
    legacy.main()
    assert called["argv"] is not None
```

- [ ] **Step 2: Run the compatibility test to verify it fails**

Run: `pytest tests/test_cli.py::test_legacy_script_entrypoint_delegates_to_new_cli -v`
Expected: FAIL

- [ ] **Step 3: Replace the monolithic script body with a thin delegation layer**

```python
from odps_skill.cli import main


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Run the compatibility test**

Run: `pytest tests/test_cli.py::test_legacy_script_entrypoint_delegates_to_new_cli -v`
Expected: PASS

- [ ] **Step 5: Commit the compatibility shim**

```bash
git add scripts/odps_query.py tests/test_cli.py
git commit -m "refactor: keep legacy script as cli shim"
```

### Task 12: Rewrite `SKILL.md` and `README.md` to match the implemented contract

**Files:**
- Modify: `SKILL.md`
- Modify: `README.md`

- [ ] **Step 1: Rewrite `SKILL.md` as an OpenClaw protocol document**

Include:

- When agents should use the skill
- Explicit non-goals
- Recommended command flow
- JSON-first output expectations
- Failure and diagnostics behavior

- [ ] **Step 2: Rewrite `README.md` for humans using the same contract**

Include:

- Installation
- Configuration
- Example `list`, `describe`, and `query` commands
- `--output json|text|table`
- Compatibility note for the legacy script path

- [ ] **Step 3: Add command examples that match the real implementation**

```bash
odps-skill list --project demo --output json
odps-skill describe --project demo --table orders --output json
odps-skill query --project demo --sql "SELECT * FROM orders LIMIT 10" --output json
```

- [ ] **Step 4: Review both docs against the spec for terminology drift**

Run: `rg -n "MCP|remote service|SQL generation|write operation" SKILL.md README.md`
Expected: References only where they are explicitly documented as out of scope or unsupported

- [ ] **Step 5: Commit the documentation updates**

```bash
git add SKILL.md README.md
git commit -m "docs: rewrite skill and readme for local agent use"
```

### Task 13: Run the full test suite and verify the working tree is clean

**Files:**
- Modify: `tests/test_cli.py`
- Modify: `tests/test_config.py`
- Modify: `tests/test_metadata.py`
- Modify: `tests/test_query_guardrails.py`
- Modify: `tests/test_formatters.py`
- Modify: `tests/test_diagnostics.py`

- [ ] **Step 1: Run the focused unit suite**

Run: `pytest tests/test_cli.py tests/test_config.py tests/test_metadata.py tests/test_query_guardrails.py tests/test_formatters.py tests/test_diagnostics.py -v`
Expected: PASS

- [ ] **Step 2: Fix any contract drift revealed by the suite**

If failures appear, update the smallest affected implementation or test file and rerun the failing command before rerunning the full suite.

- [ ] **Step 3: Run a final smoke test through the CLI**

Run:

```bash
python scripts/odps_query.py list --project demo --output json
python scripts/odps_query.py describe --project demo --table orders --output text
python scripts/odps_query.py query --project demo --sql "SELECT 1" --output json
```

Expected:

- Legacy path reaches the new CLI
- JSON output is valid
- Text output is readable

- [ ] **Step 4: Verify the tree is clean**

Run: `git status --short`
Expected: no output

- [ ] **Step 5: Commit final polish if needed**

```bash
git add .
git commit -m "test: finalize odps skill contract coverage"
```
