from __future__ import annotations

import sys
from pathlib import Path

from mdcheck.constants import DEFAULT_HTTP_TIMEOUT_SECONDS
from mdcheck.discovery import discover_markdown_files
from mdcheck.models import AnchorCache, CheckResult, CheckStats, Finding, FindingKind, LinkKind, UrlCache
from mdcheck.parser import extract_links
from mdcheck.validators import create_http_session, validate_local_link, validate_url_link


def run_check(
    root: Path,
    *,
    check_urls: bool,
    verbose: bool,
) -> CheckResult:
    resolved_root = root.expanduser().resolve()
    if not resolved_root.exists():
        raise FileNotFoundError(f"Scan root does not exist: {resolved_root}")
    if not resolved_root.is_dir():
        raise NotADirectoryError(f"Scan root is not a directory: {resolved_root}")

    if verbose:
        print(f"Scanning root: {resolved_root}", file=sys.stderr)

    markdown_files = discover_markdown_files(resolved_root)
    if verbose:
        print(f"Discovered {len(markdown_files)} Markdown files", file=sys.stderr)

    anchor_cache: AnchorCache = {}
    url_cache: UrlCache = {}
    session = create_http_session() if check_urls else None

    stats = CheckStats(markdown_files=len(markdown_files))
    findings: list[Finding] = []

    for markdown_file in markdown_files:
        if verbose:
            try:
                display_file = markdown_file.relative_to(resolved_root)
            except ValueError:
                display_file = markdown_file
            print(f"Checking {display_file}", file=sys.stderr)

        links = extract_links(markdown_file)
        stats.links_total += len(links)

        for link in links:
            if link.kind is LinkKind.LOCAL:
                stats.links_local += 1
                findings.extend(
                    validate_local_link(
                        link,
                        root=resolved_root,
                        anchor_cache=anchor_cache,
                    )
                )
            elif link.kind is LinkKind.URL:
                stats.links_url += 1
                if check_urls:
                    assert session is not None
                    before = len(url_cache)
                    url_findings = validate_url_link(
                        link,
                        session=session,
                        url_cache=url_cache,
                        timeout_seconds=DEFAULT_HTTP_TIMEOUT_SECONDS,
                    )
                    if link.raw_target in url_cache and len(url_cache) > before:
                        stats.urls_checked += 1
                    findings.extend(url_findings)
                else:
                    stats.urls_skipped += 1
                    if verbose:
                        print(f"Skipping URL check: {link.raw_target}", file=sys.stderr)
            elif link.kind is LinkKind.EMPTY:
                stats.links_empty += 1
                findings.append(
                    Finding(
                        kind=FindingKind.EMPTY_LINK,
                        source_file=link.source_file,
                        line=link.line,
                        target=link.raw_target,
                        message="Link target is empty.",
                    )
                )
            elif link.kind is LinkKind.UNSUPPORTED:
                stats.links_unsupported += 1
                findings.append(
                    Finding(
                        kind=FindingKind.UNSUPPORTED_SCHEME,
                        source_file=link.source_file,
                        line=link.line,
                        target=link.raw_target,
                        message=f"Unsupported link scheme: {link.raw_target}",
                    )
                )
            elif link.kind is LinkKind.EMAIL:
                continue

    stats.findings_total = len(findings)

    if verbose:
        print(f"Checked {stats.links_total} links", file=sys.stderr)
        print(f"Found {stats.findings_total} findings", file=sys.stderr)

    return CheckResult(root=resolved_root, findings=findings, stats=stats)
