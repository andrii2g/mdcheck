from __future__ import annotations

from pathlib import Path

from mdcheck.models import LinkKind
from mdcheck.parser import classify_target, extract_links


def test_classify_target_variants() -> None:
    assert classify_target("") is LinkKind.EMPTY
    assert classify_target("   ") is LinkKind.EMPTY
    assert classify_target("https://example.com") is LinkKind.URL
    assert classify_target("http://example.com") is LinkKind.URL
    assert classify_target("mailto:test@example.com") is LinkKind.EMAIL
    assert classify_target("tel:+123456") is LinkKind.UNSUPPORTED
    assert classify_target("javascript:alert(1)") is LinkKind.UNSUPPORTED
    assert classify_target("#intro") is LinkKind.LOCAL
    assert classify_target("./guide.md#intro") is LinkKind.LOCAL
    assert classify_target("/docs/index.md") is LinkKind.LOCAL


def test_extracts_inline_image_autolink_and_reference_links(tmp_path: Path) -> None:
    markdown_file = tmp_path.resolve() / "README.md"
    markdown_file.write_text(
        "\n".join(
            [
                "[site](https://example.com)",
                "![logo](./logo.png)",
                "<https://example.org>",
                "[ref-link][ref]",
                "",
                "[ref]: ./guide.md",
            ]
        ),
        encoding="utf-8",
    )

    links = extract_links(markdown_file.resolve())

    assert [link.raw_target for link in links] == [
        "https://example.com",
        "./logo.png",
        "https://example.org",
        "./guide.md",
    ]
    assert [link.kind for link in links] == [
        LinkKind.URL,
        LinkKind.LOCAL,
        LinkKind.URL,
        LinkKind.LOCAL,
    ]
    assert [link.line for link in links] == [1, 2, 3, 4]
    assert all(link.source_file == markdown_file.resolve() for link in links)
    assert links[1].is_image is True


def test_extracts_empty_target_and_preserves_source_order(tmp_path: Path) -> None:
    markdown_file = tmp_path.resolve() / "doc.md"
    markdown_file.write_text(
        "\n".join(
            [
                "[empty]()",
                "[local](./guide.md)",
                "[email](mailto:test@example.com)",
            ]
        ),
        encoding="utf-8",
    )

    links = extract_links(markdown_file.resolve())

    assert [link.raw_target for link in links] == ["", "./guide.md", "mailto:test@example.com"]
    assert [link.kind for link in links] == [
        LinkKind.EMPTY,
        LinkKind.LOCAL,
        LinkKind.EMAIL,
    ]
