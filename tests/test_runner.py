from __future__ import annotations

from pathlib import Path

from mdcheck.runner import run_check


def test_run_check_skips_url_requests_when_disabled(tmp_path: Path) -> None:
    root = tmp_path.resolve()
    readme = root / "README.md"
    readme.write_text("[site](https://example.com)\n", encoding="utf-8")

    result = run_check(root, check_urls=False, verbose=False)

    assert result.stats.markdown_files == 1
    assert result.stats.links_url == 1
    assert result.stats.urls_skipped == 1
    assert result.findings == []


def test_run_check_still_validates_local_links_when_urls_disabled(tmp_path: Path) -> None:
    root = tmp_path.resolve()
    readme = root / "README.md"
    readme.write_text("[missing](./missing.md)\n", encoding="utf-8")

    result = run_check(root, check_urls=False, verbose=False)

    assert result.stats.links_local == 1
    assert result.stats.findings_total == 1
    assert result.findings[0].kind.value == "MISSING_FILE"


def test_run_check_returns_findings_and_stats_for_mixed_links(tmp_path: Path) -> None:
    root = tmp_path.resolve()
    docs = root / "docs"
    docs.mkdir()
    readme = root / "README.md"
    guide = docs / "guide.md"
    guide.write_text("# Intro\n", encoding="utf-8")
    readme.write_text(
        "\n".join(
            [
                "[ok](./docs/guide.md#intro)",
                "[broken-anchor](./docs/guide.md#missing)",
                "[empty]()",
                "[js](javascript:alert(1))",
            ]
        ),
        encoding="utf-8",
    )

    result = run_check(root, check_urls=False, verbose=False)

    assert result.stats.markdown_files == 2
    assert result.stats.links_total == 4
    assert result.stats.links_local == 2
    assert result.stats.links_empty == 1
    assert result.stats.links_unsupported == 1
    assert result.stats.findings_total == 3
