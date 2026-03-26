#!/usr/bin/env python3
"""Compatibility shim for the local ODPS skill CLI."""

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from odps_skill.cli import main as cli_main


def main(argv=None) -> int:
    return cli_main(sys.argv[1:] if argv is None else argv)


if __name__ == "__main__":
    raise SystemExit(main())
