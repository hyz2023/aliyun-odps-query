import argparse
import json

from odps_skill.client import DependencyMissingError
from odps_skill.client import create_client
from odps_skill.config import load_config
from odps_skill.diagnostics import build_diagnostics
from odps_skill.diagnostics import build_summary
from odps_skill.formatters import render
from odps_skill.metadata import MetadataService
from odps_skill.query import InvalidQueryError
from odps_skill.query import execute_query
from odps_skill.query import validate_read_only_sql
from odps_skill.schemas import error_response
from odps_skill.schemas import success_response


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="odps-skill")
    subparsers = parser.add_subparsers(dest="command", required=True)
    for name in ("list", "describe", "query", "summarize", "diagnose"):
        subparser = subparsers.add_parser(name)
        if name in {"list", "describe", "query"}:
            subparser.add_argument("--project", required=True)
        if name == "list":
            subparser.add_argument("--pattern")
        if name == "describe":
            subparser.add_argument("--table")
        if name == "query":
            subparser.add_argument("--sql")
        if name == "summarize":
            subparser.add_argument("--input-json")
        if name == "diagnose":
            subparser.add_argument("--error-type")
        subparser.add_argument("--output", choices=["json", "text", "table"], default="json")
    return parser


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    try:
        data = {}
        meta = {}
        if args.command in {"list", "describe"}:
            config = load_config(project=args.project)
            metadata_service = MetadataService(create_client(config))
            if args.command == "list":
                data = metadata_service.list_tables(pattern=args.pattern)
            elif not args.table:
                raise SystemExit("describe requires --table")
            else:
                data = metadata_service.describe_table(args.table)
        elif args.command == "query":
            if not args.sql:
                raise SystemExit("query requires --sql")
            validate_read_only_sql(args.sql)
            config = load_config(project=args.project)
            data = execute_query(client=create_client(config), project=args.project, sql=args.sql)
            meta = {"row_count": data.get("count", 0), "truncated": False}
        elif args.command == "summarize":
            if not args.input_json:
                raise SystemExit("summarize requires --input-json")
            data = json.loads(args.input_json)
            payload = success_response(
                action=args.command,
                project=None,
                data=data,
                summary=build_summary(action="query", data=data, meta={}),
                diagnostics=[],
                meta={},
            )
            print(render(payload, output=args.output))
            return 0
        elif args.command == "diagnose":
            if not args.error_type:
                raise SystemExit("diagnose requires --error-type")
            diagnostics = build_diagnostics(error_type=args.error_type, context={"action": "query"})
            payload = success_response(
                action=args.command,
                project=None,
                data={"diagnostics": diagnostics},
                summary="Diagnostics generated.",
                diagnostics=diagnostics,
                meta={},
            )
            print(render(payload, output=args.output))
            return 0
        else:
            data = {}

        payload = success_response(
            action=args.command,
            project=getattr(args, "project", None),
            data=data,
            summary=build_summary(action=args.command, data=data, meta=meta),
            diagnostics=[],
            meta=meta,
        )
        exit_code = 0
    except InvalidQueryError as exc:
        payload = error_response(
            action=args.command,
            project=getattr(args, "project", None),
            error_type="invalid_query",
            message=str(exc),
            diagnostics=build_diagnostics(error_type="invalid_query", context={"action": args.command}),
        )
        exit_code = 1
    except DependencyMissingError as exc:
        payload = error_response(
            action=args.command,
            project=getattr(args, "project", None),
            error_type="dependency_missing",
            message=str(exc),
            diagnostics=build_diagnostics(error_type="dependency_missing", context={"action": args.command}),
        )
        exit_code = 1

    print(render(payload, output=args.output))
    return exit_code
