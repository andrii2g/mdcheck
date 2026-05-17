from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from urllib.parse import unquote, urlsplit

import requests

from mdcheck.anchors import get_anchors
from mdcheck.constants import DEFAULT_USER_AGENT
from mdcheck.models import AnchorCache, Finding, FindingKind, Link, UrlCache


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


def create_http_session(user_agent: str = DEFAULT_USER_AGENT) -> requests.Session:
    session = requests.Session()
    session.headers.update({"User-Agent": user_agent})
    return session


def validate_url_link(
    link: Link,
    *,
    session: requests.Session,
    url_cache: UrlCache,
    timeout_seconds: float,
) -> list[Finding]:
    cache_key = link.raw_target
    if cache_key in url_cache:
        return list(url_cache[cache_key])

    findings = _validate_url_uncached(
        link,
        session=session,
        timeout_seconds=timeout_seconds,
    )
    url_cache[cache_key] = findings
    return list(findings)


def _validate_url_uncached(
    link: Link,
    *,
    session: requests.Session,
    timeout_seconds: float,
) -> list[Finding]:
    try:
        head_response = session.head(
            link.raw_target,
            allow_redirects=True,
            timeout=timeout_seconds,
        )
    except requests.Timeout:
        return [_timeout_finding(link)]
    except requests.RequestException:
        return _validate_url_with_get(link, session=session, timeout_seconds=timeout_seconds)

    if head_response.status_code < 400:
        return []

    if head_response.status_code in {403, 405, 406}:
        return _validate_url_with_get(link, session=session, timeout_seconds=timeout_seconds)

    return [_broken_url_finding(link, head_response.status_code)]


def _validate_url_with_get(
    link: Link,
    *,
    session: requests.Session,
    timeout_seconds: float,
) -> list[Finding]:
    try:
        response = session.get(
            link.raw_target,
            allow_redirects=True,
            timeout=timeout_seconds,
        )
    except requests.Timeout:
        return [_timeout_finding(link)]
    except requests.RequestException as exc:
        return [_url_error_finding(link, str(exc))]

    if response.status_code < 400:
        return []

    return [_broken_url_finding(link, response.status_code)]


def _broken_url_finding(link: Link, status_code: int) -> Finding:
    return Finding(
        kind=FindingKind.BROKEN_URL,
        source_file=link.source_file,
        line=link.line,
        target=link.raw_target,
        message=f"HTTP {status_code} for {link.raw_target}",
        status_code=status_code,
    )


def _timeout_finding(link: Link) -> Finding:
    return Finding(
        kind=FindingKind.URL_TIMEOUT,
        source_file=link.source_file,
        line=link.line,
        target=link.raw_target,
        message=f"Timeout while checking {link.raw_target}",
    )


def _url_error_finding(link: Link, detail: str) -> Finding:
    return Finding(
        kind=FindingKind.URL_ERROR,
        source_file=link.source_file,
        line=link.line,
        target=link.raw_target,
        message=f"URL error for {link.raw_target}: {detail}",
    )
