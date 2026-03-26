import argparse

from odps_skill.schemas import success_response


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="odps-skill")
    subparsers = parser.add_subparsers(dest="command", required=True)
    for name in ("list", "describe", "query", "summarize", "diagnose"):
        subparsers.add_parser(name)
    return parser


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    success_response(action=args.command, project=getattr(args, "project", None), data={})
    return 0
