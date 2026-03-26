#!/usr/bin/env python3
"""Compatibility shim for the local ODPS skill CLI."""

import sys

from odps_skill.cli import main as cli_main


def main(argv=None) -> int:
    return cli_main(sys.argv[1:] if argv is None else argv)


if __name__ == "__main__":
    raise SystemExit(main())
