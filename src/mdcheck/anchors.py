from __future__ import annotations

import re
import string
from pathlib import Path

from markdown_it import MarkdownIt
from markdown_it.token import Token

from mdcheck.models import AnchorCache


_MARKDOWN_IT = MarkdownIt("commonmark")
_INLINE_FORMATTING = str.maketrans("", "", "*_`[]")
_PUNCTUATION = string.punctuation.replace("-", "")
_PUNCTUATION_TABLE = str.maketrans("", "", _PUNCTUATION)
_TRAILING_CUSTOM_ID_RE = re.compile(r"\s+\{#[^}]+\}\s*$")


def get_anchors(markdown_file: Path, *, anchor_cache: AnchorCache) -> set[str]:
    if markdown_file in anchor_cache:
        return anchor_cache[markdown_file]

    anchors = extract_anchors(markdown_file)
    anchor_cache[markdown_file] = anchors
    return anchors


def extract_anchors(markdown_file: Path) -> set[str]:
    text = markdown_file.read_text(encoding="utf-8")
    tokens = _MARKDOWN_IT.parse(text)
    anchors: set[str] = set()
    existing: dict[str, int] = {}

    for index, token in enumerate(tokens):
        if token.type != "heading_open":
            continue
        if token.tag not in {"h1", "h2", "h3", "h4", "h5", "h6"}:
            continue
        if index + 1 >= len(tokens):
            continue
        inline = tokens[index + 1]
        if inline.type != "inline":
            continue
        slug = github_slugify(inline.content, existing=existing)
        if slug:
            anchors.add(slug)

    return anchors


def github_slugify(heading_text: str, *, existing: dict[str, int]) -> str:
    text = _TRAILING_CUSTOM_ID_RE.sub("", heading_text).lower().strip()
    text = text.translate(_INLINE_FORMATTING)
    text = text.translate(_PUNCTUATION_TABLE)
    text = re.sub(r"\s+", "-", text)
    text = re.sub(r"-{2,}", "-", text)
    base = text.strip("-")
    count = existing.get(base, 0)
    existing[base] = count + 1
    if count == 0:
        return base
    return f"{base}-{count}"
