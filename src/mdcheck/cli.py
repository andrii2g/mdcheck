from __future__ import annotations

import argparse
from collections.abc import Sequence
from pathlib import Path
import sys

from mdcheck.constants import APP_NAME, VERSION
from mdcheck.report import format_report, write_report
from mdcheck.runner import run_check


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog=APP_NAME,
        description="Validate local and remote links in Markdown files.",
    )
    parser.add_argument("path", nargs="?", metavar="PATH", help="Folder to scan.")
    parser.add_argument(
        "--report",
        metavar="PATH",
        help="Write Markdown report to PATH.",
    )
    parser.add_argument(
        "--no-url-check",
        action="store_true",
        help="Skip HTTP/HTTPS validation.",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print progress to stderr.",
    )
    parser.add_argument(
        "--version",
        action="store_true",
        help="Print version and exit.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.version:
        print(f"{APP_NAME} {VERSION}")
        return 0

    if not args.path:
        parser.error("the following arguments are required: PATH")

    try:
        result = run_check(
            Path(args.path),
            check_urls=not args.no_url_check,
            verbose=args.verbose,
        )
    except Exception as exc:
        print(f"{APP_NAME}: {exc}", file=sys.stderr)
        return 2

    report = format_report(result)
    if args.report:
        report_path = Path(args.report)
        write_report(report, report_path)
        print(f"Wrote report to {report_path}")
        print(f"Findings: {result.stats.findings_total}")
    else:
        print(report, end="")

    return 1 if result.findings else 0
