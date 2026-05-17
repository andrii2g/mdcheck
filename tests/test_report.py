from __future__ import annotations

from pathlib import Path

from mdcheck.models import CheckResult, CheckStats, Finding, FindingKind
from mdcheck.report import format_report, write_report


def test_format_report_with_no_findings(tmp_path: Path) -> None:
    root = tmp_path.resolve()
    result = CheckResult(root=root, findings=[], stats=CheckStats(markdown_files=1))

    report = format_report(result)

    assert "# mdcheck report" in report
    assert "## Findings" in report
    assert "No findings." in report


def test_format_report_with_findings_and_escaping(tmp_path: Path) -> None:
    root = tmp_path.resolve()
    finding = Finding(
        kind=FindingKind.BROKEN_URL,
        source_file=(root / "README.md").resolve(),
        line=42,
        target="https://example.com/old|page",
        message="HTTP 404 | missing",
        status_code=404,
    )
    result = CheckResult(
        root=root,
        findings=[finding],
        stats=CheckStats(markdown_files=1, findings_total=1),
    )

    report = format_report(result)

    assert "| BROKEN_URL |" in report
    assert "`README.md`" in report
    assert "old\\|page" in report
    assert "404 \\| missing" in report


def test_write_report_creates_parent_directories(tmp_path: Path) -> None:
    report_path = tmp_path / "reports" / "mdcheck.md"

    write_report("# report\n", report_path)

    assert report_path.read_text(encoding="utf-8") == "# report\n"


def test_format_report_uses_absolute_path_when_outside_root(tmp_path: Path) -> None:
    root = tmp_path.resolve()
    external = Path("C:/external/README.md")
    finding = Finding(
        kind=FindingKind.MISSING_FILE,
        source_file=external,
        line=3,
        target="./missing.md",
        message="Local path was not found: ./missing.md",
    )
    result = CheckResult(
        root=root,
        findings=[finding],
        stats=CheckStats(markdown_files=1, findings_total=1),
    )

    report = format_report(result)

    assert "C:/external/README.md" in report or "C:\\external\\README.md" in report
