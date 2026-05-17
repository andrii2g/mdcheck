from __future__ import annotations

from pathlib import Path
from urllib.parse import urlsplit

from markdown_it import MarkdownIt
from markdown_it.token import Token

from mdcheck.models import Link, LinkKind


def classify_target(raw_target: str) -> LinkKind:
    target = raw_target.strip()
    if not target:
        return LinkKind.EMPTY

    scheme = urlsplit(target).scheme.lower()
    if not scheme:
        return LinkKind.LOCAL
    if scheme in {"http", "https"}:
        return LinkKind.URL
    if scheme == "mailto":
        return LinkKind.EMAIL
    return LinkKind.UNSUPPORTED


def extract_links(markdown_file: Path) -> list[Link]:
    text = markdown_file.read_text(encoding="utf-8")
    parser = MarkdownIt("commonmark")
    tokens = parser.parse(text)
    links: list[Link] = []
    _walk_tokens(tokens, markdown_file, links, inherited_line=1)
    return links


def _walk_tokens(
    tokens: list[Token],
    markdown_file: Path,
    links: list[Link],
    *,
    inherited_line: int,
) -> None:
    for token in tokens:
        line = _line_for_token(token, inherited_line)
        if token.type == "link_open":
            raw_target = token.attrGet("href") or ""
            links.append(
                Link(
                    source_file=markdown_file,
                    line=line,
                    raw_target=raw_target.strip(),
                    text="",
                    kind=classify_target(raw_target),
                )
            )
        elif token.type == "image":
            raw_target = token.attrGet("src") or ""
            links.append(
                Link(
                    source_file=markdown_file,
                    line=line,
                    raw_target=raw_target.strip(),
                    text=token.content,
                    kind=classify_target(raw_target),
                    is_image=True,
                )
            )

        if token.children:
            _walk_tokens(token.children, markdown_file, links, inherited_line=line)


def _line_for_token(token: Token, inherited_line: int) -> int:
    if token.map:
        return token.map[0] + 1
    return inherited_line
