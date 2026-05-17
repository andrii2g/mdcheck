from __future__ import annotations

import argparse
from collections.abc import Sequence

from mdcheck.constants import APP_NAME, VERSION


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog=APP_NAME)
    parser.add_argument("path", metavar="PATH", help="Path to the folder to scan.")
    parser.add_argument(
        "--report",
        metavar="PATH",
        help="Write the Markdown report to PATH instead of only printing it to stdout.",
    )
    parser.add_argument(
        "--no-url-check",
        action="store_true",
        help="Skip HTTP/HTTPS validation. Local path and anchor checks still run.",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print progress and diagnostic information to stderr.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"{APP_NAME} {VERSION}",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    parser.parse_args(argv)
    return 0
