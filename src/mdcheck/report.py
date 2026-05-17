from __future__ import annotations

from pathlib import Path

from mdcheck.models import CheckResult, Finding


def format_report(result: CheckResult) -> str:
    lines = [
        "# mdcheck report",
        "",
        f"Root: `{format_path_for_report(result.root, root=result.root)}`",
        "",
        "## Summary",
        "",
        "| Metric | Count |",
        "|---|---:|",
        f"| Markdown files | {result.stats.markdown_files} |",
        f"| Links total | {result.stats.links_total} |",
        f"| Local links | {result.stats.links_local} |",
        f"| URL links | {result.stats.links_url} |",
        f"| URLs checked | {result.stats.urls_checked} |",
        f"| URLs skipped | {result.stats.urls_skipped} |",
        f"| Findings | {result.stats.findings_total} |",
        "",
        "## Findings",
        "",
    ]

    if not result.findings:
        lines.append("No findings.")
        return "\n".join(lines) + "\n"

    lines.extend(
        [
            "| Type | Source | Line | Target | Detail |",
            "|---|---|---:|---|---|",
        ]
    )
    for finding in result.findings:
        lines.append(_format_finding_row(finding, root=result.root))

    return "\n".join(lines) + "\n"


def write_report(report: str, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(report, encoding="utf-8", newline="\n")


def format_path_for_report(path: Path, *, root: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


def _format_finding_row(finding: Finding, *, root: Path) -> str:
    source = _escape_markdown_cell(format_path_for_report(finding.source_file, root=root))
    target = _escape_markdown_cell(finding.target)
    detail = _escape_markdown_cell(finding.message)
    return (
        f"| {finding.kind.value} | `{source}` | {finding.line} | `{target}` | {detail} |"
    )


def _escape_markdown_cell(value: str) -> str:
    return value.replace("\\", "\\\\").replace("|", "\\|").replace("\n", " ").replace("`", "\\`")
