import argparse


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="odps-skill")
    subparsers = parser.add_subparsers(dest="command", required=True)
    for name in ("list", "describe", "query", "summarize", "diagnose"):
        subparsers.add_parser(name)
    return parser


def main(argv=None) -> int:
    build_parser().parse_args(argv)
    return 0
