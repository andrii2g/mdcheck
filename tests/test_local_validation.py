from __future__ import annotations

from pathlib import Path

from mdcheck.models import FindingKind, Link, LinkKind
from mdcheck.validators import resolve_local_target, validate_local_link


def _make_link(source_file: Path, raw_target: str) -> Link:
    return Link(
        source_file=source_file.resolve(),
        line=1,
        raw_target=raw_target,
        text="",
        kind=LinkKind.LOCAL,
    )


def test_resolve_local_target_handles_relative_root_relative_and_fragment(tmp_path: Path) -> None:
    root = tmp_path.resolve()
    source_file = root / "docs" / "a.md"
    source_file.parent.mkdir()
    source_file.write_text("# A\n", encoding="utf-8")

    relative = resolve_local_target(_make_link(source_file, "b.md#intro"), root=root)
    root_relative = resolve_local_target(_make_link(source_file, "/README.md"), root=root)
    fragment_only = resolve_local_target(_make_link(source_file, "#intro"), root=root)

    assert relative.target_path == (root / "docs" / "b.md").resolve()
    assert relative.anchor == "intro"
    assert root_relative.target_path == (root / "README.md").resolve()
    assert root_relative.anchor is None
    assert fragment_only.target_path == source_file.resolve()
    assert fragment_only.anchor == "intro"


def test_existing_local_file_passes(tmp_path: Path) -> None:
    root = tmp_path.resolve()
    source_file = root / "docs" / "a.md"
    target_file = root / "docs" / "guide.md"
    source_file.parent.mkdir()
    source_file.write_text("# A\n", encoding="utf-8")
    target_file.write_text("# Guide\n", encoding="utf-8")

    findings = validate_local_link(
        _make_link(source_file, "./guide.md"),
        root=root,
        anchor_cache={},
    )

    assert findings == []


def test_missing_local_file_returns_missing_file(tmp_path: Path) -> None:
    root = tmp_path.resolve()
    source_file = root / "docs" / "a.md"
    source_file.parent.mkdir()
    source_file.write_text("# A\n", encoding="utf-8")

    findings = validate_local_link(
        _make_link(source_file, "./missing.md"),
        root=root,
        anchor_cache={},
    )

    assert len(findings) == 1
    assert findings[0].kind is FindingKind.MISSING_FILE


def test_missing_markdown_anchor_returns_broken_anchor(tmp_path: Path) -> None:
    root = tmp_path.resolve()
    source_file = root / "docs" / "a.md"
    target_file = root / "docs" / "guide.md"
    source_file.parent.mkdir()
    source_file.write_text("# A\n", encoding="utf-8")
    target_file.write_text("# Intro\n", encoding="utf-8")

    findings = validate_local_link(
        _make_link(source_file, "./guide.md#missing"),
        root=root,
        anchor_cache={},
    )

    assert len(findings) == 1
    assert findings[0].kind is FindingKind.BROKEN_ANCHOR


def test_directory_target_is_valid(tmp_path: Path) -> None:
    root = tmp_path.resolve()
    source_file = root / "docs" / "a.md"
    target_dir = root / "assets"
    source_file.parent.mkdir()
    target_dir.mkdir()
    source_file.write_text("# A\n", encoding="utf-8")

    findings = validate_local_link(
        _make_link(source_file, "../assets"),
        root=root,
        anchor_cache={},
    )

    assert findings == []


def test_anchor_cache_is_used_on_repeated_calls(tmp_path: Path) -> None:
    root = tmp_path.resolve()
    source_file = root / "docs" / "a.md"
    target_file = root / "docs" / "guide.md"
    source_file.parent.mkdir()
    source_file.write_text("# A\n", encoding="utf-8")
    target_file.write_text("# Intro\n", encoding="utf-8")
    anchor_cache: dict[Path, set[str]] = {}

    first = validate_local_link(
        _make_link(source_file, "./guide.md#intro"),
        root=root,
        anchor_cache=anchor_cache,
    )
    target_file.write_text("# Changed\n", encoding="utf-8")
    second = validate_local_link(
        _make_link(source_file, "./guide.md#intro"),
        root=root,
        anchor_cache=anchor_cache,
    )

    assert first == []
    assert second == []
    assert target_file.resolve() in anchor_cache
