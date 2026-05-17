from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def run_module(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "mdcheck", *args],
        cwd=ROOT,
        text=True,
        capture_output=True,
        env={
            **os.environ,
            "PYTHONPATH": str(ROOT / "src"),
        },
    )


def test_version_output() -> None:
    result = run_module("--version")

    assert result.returncode == 0
    assert result.stdout.strip() == "mdcheck 0.1.0"
    assert result.stderr == ""


def test_help_contains_only_approved_options() -> None:
    result = run_module("--help")

    assert result.returncode == 0
    assert "PATH" in result.stdout
    assert "--report" in result.stdout
    assert "--no-url-check" in result.stdout
    assert "--verbose" in result.stdout
    assert "--version" in result.stdout
    assert "--timeout" not in result.stdout
    assert "--user-agent" not in result.stdout
    assert "--include-hidden" not in result.stdout


def test_path_is_required() -> None:
    result = run_module()

    assert result.returncode == 2
    assert "PATH" in result.stderr


def test_default_run_prints_markdown_report_and_returns_findings_exit_code(tmp_path: Path) -> None:
    readme = tmp_path / "README.md"
    readme.write_text("[missing](./missing.md)\n", encoding="utf-8")

    result = run_module(str(tmp_path))

    assert result.returncode == 1
    assert "# mdcheck report" in result.stdout
    assert "MISSING_FILE" in result.stdout


def test_report_option_writes_file_and_prints_summary(tmp_path: Path) -> None:
    readme = tmp_path / "README.md"
    report_path = tmp_path / "out" / "mdcheck.md"
    readme.write_text("# ok\n", encoding="utf-8")

    result = run_module(str(tmp_path), "--report", str(report_path))

    assert result.returncode == 0
    assert report_path.exists()
    assert "# mdcheck report" in report_path.read_text(encoding="utf-8")
    assert "Wrote report to" in result.stdout
