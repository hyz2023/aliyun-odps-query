import argparse

from odps_skill.client import create_client
from odps_skill.config import load_config
from odps_skill.formatters import render
from odps_skill.metadata import MetadataService
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
        subparser.add_argument("--output", choices=["json", "text", "table"], default="json")
    return parser


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    data = {}
    if args.command == "list":
        config = load_config(project=args.project)
        metadata_service = MetadataService(create_client(config))
        data = metadata_service.list_tables(pattern=args.pattern)

    payload = success_response(action=args.command, project=getattr(args, "project", None), data=data)
    print(render(payload, output=args.output))
    return 0
