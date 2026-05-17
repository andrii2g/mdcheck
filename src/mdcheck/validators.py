from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from urllib.parse import unquote, urlsplit

from mdcheck.anchors import get_anchors
from mdcheck.models import AnchorCache, Finding, FindingKind, Link


@dataclass(frozen=True)
class LocalTarget:
    target_path: Path
    anchor: str | None


def resolve_local_target(link: Link, *, root: Path) -> LocalTarget:
    split = urlsplit(link.raw_target)
    path_part = unquote(split.path)
    anchor = unquote(split.fragment) or None

    if link.raw_target.startswith("#"):
        target_path = link.source_file
    elif path_part.startswith("/"):
        target_path = (root / path_part.lstrip("/")).resolve()
    else:
        relative = path_part or "."
        target_path = (link.source_file.parent / relative).resolve()

    return LocalTarget(target_path=target_path, anchor=anchor)


def validate_local_link(
    link: Link,
    *,
    root: Path,
    anchor_cache: AnchorCache,
) -> list[Finding]:
    local_target = resolve_local_target(link, root=root)
    target_path = local_target.target_path

    if not target_path.exists():
        return [
            Finding(
                kind=FindingKind.MISSING_FILE,
                source_file=link.source_file,
                line=link.line,
                target=link.raw_target,
                message=f"Local path was not found: {link.raw_target}",
            )
        ]

    if local_target.anchor is None:
        return []

    if target_path.is_dir():
        return []

    if target_path.suffix.lower() not in {".md", ".markdown"}:
        return []

    anchors = get_anchors(target_path, anchor_cache=anchor_cache)
    if local_target.anchor in anchors:
        return []

    display_path = target_path
    try:
        display_path = target_path.relative_to(root)
    except ValueError:
        pass

    return [
        Finding(
            kind=FindingKind.BROKEN_ANCHOR,
            source_file=link.source_file,
            line=link.line,
            target=link.raw_target,
            message=f"Anchor '{local_target.anchor}' was not found in {display_path}.",
        )
    ]
