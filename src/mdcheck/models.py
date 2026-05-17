from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path


class LinkKind(str, Enum):
    LOCAL = "local"
    URL = "url"
    EMAIL = "email"
    UNSUPPORTED = "unsupported"
    EMPTY = "empty"


class FindingKind(str, Enum):
    EMPTY_LINK = "EMPTY_LINK"
    MISSING_FILE = "MISSING_FILE"
    BROKEN_ANCHOR = "BROKEN_ANCHOR"
    BROKEN_URL = "BROKEN_URL"
    URL_TIMEOUT = "URL_TIMEOUT"
    URL_ERROR = "URL_ERROR"
    UNSUPPORTED_SCHEME = "UNSUPPORTED_SCHEME"
    SKIPPED_URL = "SKIPPED_URL"


@dataclass(frozen=True)
class Link:
    source_file: Path
    line: int
    raw_target: str
    text: str
    kind: LinkKind
    is_image: bool = False


@dataclass(frozen=True)
class Finding:
    kind: FindingKind
    source_file: Path
    line: int
    target: str
    message: str
    status_code: int | None = None


@dataclass
class CheckStats:
    markdown_files: int = 0
    links_total: int = 0
    links_local: int = 0
    links_url: int = 0
    links_empty: int = 0
    links_unsupported: int = 0
    urls_checked: int = 0
    urls_skipped: int = 0
    findings_total: int = 0


@dataclass(frozen=True)
class CheckResult:
    root: Path
    findings: list[Finding]
    stats: CheckStats


AnchorCache = dict[Path, set[str]]
UrlCache = dict[str, list[Finding]]
