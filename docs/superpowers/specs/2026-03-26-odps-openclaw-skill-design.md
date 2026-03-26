# ODPS OpenClaw Skill Design

Date: 2026-03-26
Status: Draft for review

## Goal

Refactor the current local ODPS query project into a strong OpenClaw skill for use by OpenClaw agents on the same machine.

The skill should be optimized for:

- Stable local CLI invocation from other agents
- Predictable machine-readable output
- Lightweight result summaries and diagnostics
- Low maintenance cost

The skill should not be optimized for:

- Remote service exposure
- Cross-machine distribution
- MCP server deployment in phase 1
- SQL generation
- Write or delete operations

## Context

The current project is a single Python script plus a human-oriented `SKILL.md`.

Current strengths:

- Already connects to Alibaba Cloud ODPS / MaxCompute
- Supports table listing, schema inspection, and SQL query execution
- Has a simple command line interface

Current gaps for OpenClaw-agent use:

- Logic is concentrated in one script
- Output is primarily terminal-oriented instead of contract-oriented
- Error handling is inconsistent for machine consumers
- There is no stable response envelope
- There are no explicit diagnostics for common failure modes
- The skill contract in `SKILL.md` is written more like feature documentation than an agent protocol

## Product Decision

Phase 1 will target a local OpenClaw skill that is consumed through `SKILL.md` plus CLI commands.

The skill will:

- Remain a local command-line tool
- Default to machine-readable JSON output
- Preserve text/table output for human debugging
- Reject write/delete style SQL
- Provide result summaries and rule-based diagnostics

The skill will not:

- Generate SQL
- Expose a network service
- Support mutation statements
- Attempt heavy AI interpretation of result sets

## Users and Use Cases

Primary users are OpenClaw agents running on the current machine.

Typical use cases:

1. Discover tables in a project before asking another tool to generate SQL
2. Inspect schema and partitions before composing or validating a query
3. Execute read-only SQL and consume structured results
4. Summarize query outcomes for quick agent reasoning
5. Diagnose failures such as permission issues, missing objects, empty results, or invalid query type

## Success Criteria

The refactor is successful if:

- Another local OpenClaw agent can use the skill without reading implementation code
- CLI responses are stable enough to parse programmatically
- Common failures return a structured error object and actionable diagnostics
- Read-only guardrails reliably block mutation statements
- Human operators can still run the tool in a readable terminal mode
- The internal code layout is simple enough to extend without returning to a monolithic script

## High-Level Architecture

The external interface remains a CLI skill. Internal logic is split into focused units with clear boundaries.

### External Boundary

The supported interface is:

- `SKILL.md` as the agent usage contract
- A CLI entrypoint used by OpenClaw agents and humans

### Internal Units

#### 1. Configuration and Auth

Responsibility:

- Read configuration from environment variables and explicit CLI flags
- Validate required ODPS connection inputs

Inputs:

- Access key ID
- Access key secret
- Endpoint
- Project

Outputs:

- Validated runtime config object

#### 2. ODPS Client Factory

Responsibility:

- Create and return an authenticated ODPS client

Inputs:

- Validated runtime config

Outputs:

- Ready-to-use ODPS client instance

#### 3. Metadata Service

Responsibility:

- List tables/views
- Describe schema, partitions, and basic table metadata

Inputs:

- Project
- Optional pattern
- Table name

Outputs:

- Structured metadata payloads for `list` and `describe`

#### 4. Query Service

Responsibility:

- Validate SQL against read-only guardrails
- Execute read-only queries
- Return normalized result payloads

Inputs:

- SQL string
- Project
- Optional row limit

Outputs:

- Structured query results with rows, columns, and execution metadata

#### 5. Summary and Diagnostics Service

Responsibility:

- Produce short summaries for successful commands
- Produce actionable diagnostics for failed or suspicious outcomes

Inputs:

- Action type
- Success or error payload
- Optional context such as row count or missing fields

Outputs:

- `summary`
- `diagnostics[]`

#### 6. Formatter Layer

Responsibility:

- Render a single internal response model into `json`, `text`, or `table`

Inputs:

- Normalized response envelope
- Requested output format

Outputs:

- Serialized CLI output

#### 7. CLI Layer

Responsibility:

- Parse command arguments
- Route to service layer
- Emit normalized output
- Exit with stable success/failure semantics

Inputs:

- Command-line invocation

Outputs:

- Printed result
- Exit code

## Command Surface

Phase 1 command surface:

- `list`
- `describe`
- `query`
- `summarize`
- `diagnose`

These may be implemented as subcommands in a package entrypoint or as equivalent stable flags under a single script. The key requirement is a stable interface, not a specific parser style.

### `list`

Purpose:

- Discover candidate tables/views within a project

Expected inputs:

- `--project`
- Optional `--pattern`
- Optional `--output`

Expected outputs:

- Matching table/view list
- Count
- Optional summary

### `describe`

Purpose:

- Inspect schema and metadata before querying

Expected inputs:

- `--project`
- `--table`
- Optional `--output`

Expected outputs:

- Columns
- Partitions
- Basic metadata
- Optional summary

### `query`

Purpose:

- Execute read-only SQL and return structured results

Expected inputs:

- `--project`
- `--sql`
- Optional `--limit`
- Optional `--output`

Expected outputs:

- Column list
- Result rows
- Row count
- Truncation metadata if applicable
- Optional summary
- Diagnostics if query succeeds but result is suspicious, such as empty or truncated output

### `summarize`

Purpose:

- Summarize an existing structured result for quick agent consumption

Expected inputs:

- Structured result input from file, stdin, or an explicit CLI argument design chosen during implementation planning

Expected outputs:

- Short summary text
- Optional structured summary fields

### `diagnose`

Purpose:

- Convert known failures or ambiguous result states into next-step suggestions

Expected inputs:

- Error payload, stderr text, or structured result context from file/stdin/CLI argument design chosen during implementation planning

Expected outputs:

- Diagnostic list
- Error classification if detectable

## Output Contract

Default output format should be JSON for agent use. Text and table output remain available for human debugging.

### Required JSON Envelope

Every command should return the same top-level shape:

```json
{
  "ok": true,
  "action": "describe",
  "project": "my_project",
  "target": "user_info",
  "data": {},
  "summary": "Table has 24 columns and 2 partition fields.",
  "diagnostics": [],
  "meta": {
    "duration_ms": 420,
    "row_count": 0,
    "truncated": false
  }
}
```

Failed commands should preserve the same envelope style:

```json
{
  "ok": false,
  "action": "query",
  "project": "my_project",
  "target": null,
  "data": null,
  "summary": "Query execution failed.",
  "diagnostics": [
    "Check whether the AccessKey has permission to read this project.",
    "Verify the project and table names are correct."
  ],
  "error": {
    "type": "permission_denied",
    "message": "Access denied to project my_project",
    "retryable": false
  },
  "meta": {
    "duration_ms": 180
  }
}
```

### Output Rules

- `json` is the default for agent-facing use
- `text` is concise and readable
- `table` is allowed where tabular terminal output is meaningful
- All output formats must reflect the same underlying normalized response

## Security and Guardrails

The skill is read-only.

Phase 1 guardrail policy:

- Reject mutation statements such as `INSERT`, `UPDATE`, `DELETE`, `DROP`, `ALTER`, `TRUNCATE`, and `CREATE`
- Reject obvious multi-statement input
- Return a structured `invalid_query` style error instead of attempting execution

This design intentionally does not attempt full SQL parsing in phase 1. Lightweight guardrails are sufficient for the current local skill scope and should be backed by tests.

Responsibility boundary:

- This skill blocks write/delete style operations
- This skill does not attempt to protect the caller from every expensive read query
- Upstream agents remain responsible for broader query judgment

## Error Model

Error handling should map raw exceptions and invalid states into a stable set of error types.

Initial error types:

- `auth_error`
- `permission_denied`
- `object_not_found`
- `invalid_query`
- `execution_failed`
- `empty_result`
- `dependency_missing`

### Error Mapping Requirements

- Missing credentials should not surface as raw Python tracebacks
- Missing dependency failures should explicitly name the package or capability
- Empty results should be representable as a distinguishable non-crash outcome
- Table/project lookup failures should be separated from generic execution failures

## Summary and Diagnostic Rules

This skill should provide lightweight, rule-based enhancement. It should not become a general analysis agent.

### Summary Rules

- `list`: summarize total matches and notable table/view counts
- `describe`: summarize column count, partition count, and notable schema traits if available
- `query`: summarize row count, column count, and whether output was truncated

### Diagnostic Rules

- Permission errors: suggest checking access keys and project-level permissions
- Object missing errors: suggest validating project/table/view names and calling `list` or `describe`
- Empty results: suggest checking partition filters, date ranges, and predicate strictness
- Invalid query type: state that mutation statements are not supported
- Dependency issues: suggest the exact package installation required

Diagnostics must be concise, actionable, and deterministic.

## Documentation Design

`SKILL.md` should be rewritten as an agent protocol document, not just a feature overview.

Required sections:

- What the skill is for
- What it does not do
- When an OpenClaw agent should use it
- Recommended command flow
- Command reference
- JSON output expectations
- Error and diagnostics behavior
- Example invocations for local agents

`README.md` can remain more human-oriented, but should be aligned with the actual CLI contract.

## Proposed Repository Structure

```text
aliyun-odps-query/
  SKILL.md
  README.md
  pyproject.toml
  src/odps_skill/
    __init__.py
    cli.py
    config.py
    client.py
    metadata.py
    query.py
    formatters.py
    diagnostics.py
    schemas.py
  tests/
    test_cli.py
    test_query_guardrails.py
    test_formatters.py
    test_diagnostics.py
  references/
  scripts/
```

This is a target structure, not a requirement that all packaging decisions be finalized inside the design phase. The implementation plan should decide the exact entrypoint mechanics.

## Testing Strategy

Phase 1 testing should focus on stable contracts rather than broad integration complexity.

Required test areas:

1. CLI contract tests
   - Commands return the expected response envelope
   - Success and failure paths emit stable fields

2. Guardrail tests
   - Mutation statements are rejected
   - Multi-statement inputs are rejected

3. Error mapping tests
   - Known ODPS failures map to expected error types

4. Formatter tests
   - `json`, `text`, and `table` reflect the same normalized response

5. Diagnostics tests
   - Common failures and empty results produce the expected suggestions

Live ODPS integration can remain limited and optional in phase 1 if local credentials are not always available. The important requirement is deterministic contract coverage.

## Migration Plan

### Phase 1

- Introduce package structure and CLI entrypoint
- Normalize responses
- Add read-only guardrails
- Add summaries and diagnostics
- Rewrite `SKILL.md`
- Add tests for contracts and guardrails

### Phase 2

- Improve error classification fidelity
- Expand summary coverage
- Add more robust local packaging and invocation ergonomics if needed

### Explicitly Out of Scope for Phase 1

- MCP server implementation
- Remote invocation support
- Cross-machine deployment
- SQL generation
- Full SQL AST parsing
- Query planner or cost estimation
- Heavy AI-driven result interpretation

## Risks and Mitigations

### Risk: Over-engineering the local skill

Mitigation:

- Keep the external interface CLI-first
- Keep diagnostics rule-based
- Defer MCP and service concerns

### Risk: Guardrails are too weak

Mitigation:

- Cover known mutation patterns with tests
- Make the read-only contract explicit in the skill documentation

### Risk: Internal refactor breaks existing usage

Mitigation:

- Preserve a compatible CLI path where practical
- Keep examples in `README.md` and `SKILL.md` synchronized with the implementation

### Risk: Agent consumers rely on unstable text output

Mitigation:

- Make JSON the documented default
- Treat text/table as convenience renderings only

## Open Decisions for Implementation Planning

These choices are intentionally deferred to the implementation plan because they do not change the design direction:

- Exact package/entrypoint command name
- Whether `summarize` and `diagnose` consume stdin, file input, or both
- Exact exit code mapping
- Whether the legacy script path remains as a compatibility shim

## Recommended Direction

Implement the skill as a layered local CLI package with a stable JSON-first contract, read-only guardrails, lightweight summaries, and deterministic diagnostics.

This achieves the requested goal: a strong OpenClaw-friendly ODPS skill for local agents without prematurely turning the project into a remote service or MCP server.
