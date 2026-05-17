from __future__ import annotations

from pathlib import Path

from mdcheck.discovery import discover_markdown_files


def test_discovers_markdown_suffixes(tmp_path: Path) -> None:
    docs = tmp_path / "docs"
    docs.mkdir()
    readme = tmp_path / "README.md"
    guide = docs / "guide.markdown"
    notes = docs / "notes.txt"
    readme.write_text("# readme\n", encoding="utf-8")
    guide.write_text("# guide\n", encoding="utf-8")
    notes.write_text("plain text\n", encoding="utf-8")

    result = discover_markdown_files(tmp_path.resolve())

    assert result == [readme.resolve(), guide.resolve()]


def test_skips_default_ignored_directories(tmp_path: Path) -> None:
    docs = tmp_path / "docs"
    ignored = tmp_path / "node_modules"
    docs.mkdir()
    ignored.mkdir()
    kept = docs / "guide.md"
    skipped = ignored / "package.md"
    kept.write_text("# kept\n", encoding="utf-8")
    skipped.write_text("# skipped\n", encoding="utf-8")

    result = discover_markdown_files(tmp_path.resolve())

    assert result == [kept.resolve()]


def test_returns_absolute_resolved_sorted_paths(tmp_path: Path) -> None:
    zeta = tmp_path / "zeta.md"
    alpha_dir = tmp_path / "docs"
    alpha_dir.mkdir()
    alpha = alpha_dir / "alpha.md"
    zeta.write_text("# zeta\n", encoding="utf-8")
    alpha.write_text("# alpha\n", encoding="utf-8")

    result = discover_markdown_files(tmp_path.resolve())

    assert all(path.is_absolute() for path in result)
    assert result == sorted(result, key=lambda path: str(path))
