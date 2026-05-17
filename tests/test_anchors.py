from __future__ import annotations

from pathlib import Path

from mdcheck.anchors import extract_anchors, get_anchors, github_slugify


def test_extracts_atx_heading_anchors(tmp_path: Path) -> None:
    markdown_file = tmp_path.resolve() / "README.md"
    markdown_file.write_text("# Install\n## API Client\n", encoding="utf-8")

    anchors = extract_anchors(markdown_file.resolve())

    assert anchors == {"install", "api-client"}


def test_extracts_duplicate_heading_anchors_with_suffixes(tmp_path: Path) -> None:
    markdown_file = tmp_path.resolve() / "README.md"
    markdown_file.write_text("# Install\n# Install\n# Install!\n", encoding="utf-8")

    anchors = extract_anchors(markdown_file.resolve())

    assert anchors == {"install", "install-1", "install-2"}


def test_does_not_extract_custom_id_alias_from_unsupported_syntax(tmp_path: Path) -> None:
    markdown_file = tmp_path.resolve() / "README.md"
    markdown_file.write_text("## Install {#custom-id}\n", encoding="utf-8")

    anchors = extract_anchors(markdown_file.resolve())

    assert "custom-id" not in anchors


def test_slugify_handles_punctuation_deterministically() -> None:
    existing: dict[str, int] = {}

    first = github_slugify("Hello, World!", existing=existing)
    second = github_slugify("Hello World", existing=existing)

    assert first == "hello-world"
    assert second == "hello-world-1"


def test_get_anchors_uses_cache_on_repeated_calls(tmp_path: Path) -> None:
    markdown_file = tmp_path.resolve() / "README.md"
    markdown_file.write_text("# Install\n", encoding="utf-8")
    anchor_cache: dict[Path, set[str]] = {}

    first = get_anchors(markdown_file.resolve(), anchor_cache=anchor_cache)
    markdown_file.write_text("# Changed\n", encoding="utf-8")
    second = get_anchors(markdown_file.resolve(), anchor_cache=anchor_cache)

    assert first == {"install"}
    assert second == {"install"}
    assert anchor_cache[markdown_file.resolve()] == {"install"}
