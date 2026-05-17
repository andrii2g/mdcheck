from __future__ import annotations

from pathlib import Path

import requests

from mdcheck.constants import DEFAULT_USER_AGENT
from mdcheck.models import FindingKind, Link, LinkKind
from mdcheck.validators import create_http_session, validate_url_link


class FakeResponse:
    def __init__(self, status_code: int) -> None:
        self.status_code = status_code


class FakeSession:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str, bool, float]] = []
        self._head_result: object = FakeResponse(200)
        self._get_result: object = FakeResponse(200)

    def head(self, url: str, *, allow_redirects: bool, timeout: float) -> FakeResponse:
        self.calls.append(("HEAD", url, allow_redirects, timeout))
        if isinstance(self._head_result, Exception):
            raise self._head_result
        return self._head_result

    def get(self, url: str, *, allow_redirects: bool, timeout: float) -> FakeResponse:
        self.calls.append(("GET", url, allow_redirects, timeout))
        if isinstance(self._get_result, Exception):
            raise self._get_result
        return self._get_result


def _make_link(url: str) -> Link:
    return Link(
        source_file=Path("C:/repo/README.md"),
        line=1,
        raw_target=url,
        text="",
        kind=LinkKind.URL,
    )


def test_create_http_session_uses_default_user_agent() -> None:
    session = create_http_session()

    assert session.headers["User-Agent"] == DEFAULT_USER_AGENT


def test_validate_url_link_accepts_successful_head() -> None:
    session = FakeSession()
    url_cache: dict[str, list] = {}

    findings = validate_url_link(
        _make_link("https://example.com"),
        session=session,  # type: ignore[arg-type]
        url_cache=url_cache,
        timeout_seconds=10.0,
    )

    assert findings == []
    assert session.calls == [("HEAD", "https://example.com", True, 10.0)]


def test_validate_url_link_falls_back_to_get_for_405() -> None:
    session = FakeSession()
    session._head_result = FakeResponse(405)
    session._get_result = FakeResponse(200)

    findings = validate_url_link(
        _make_link("https://example.com"),
        session=session,  # type: ignore[arg-type]
        url_cache={},
        timeout_seconds=10.0,
    )

    assert findings == []
    assert session.calls == [
        ("HEAD", "https://example.com", True, 10.0),
        ("GET", "https://example.com", True, 10.0),
    ]


def test_validate_url_link_reports_broken_url_for_404() -> None:
    session = FakeSession()
    session._head_result = FakeResponse(404)

    findings = validate_url_link(
        _make_link("https://example.com/missing"),
        session=session,  # type: ignore[arg-type]
        url_cache={},
        timeout_seconds=10.0,
    )

    assert len(findings) == 1
    assert findings[0].kind is FindingKind.BROKEN_URL
    assert findings[0].status_code == 404


def test_validate_url_link_reports_timeout() -> None:
    session = FakeSession()
    session._head_result = requests.Timeout("timed out")

    findings = validate_url_link(
        _make_link("https://example.com/slow"),
        session=session,  # type: ignore[arg-type]
        url_cache={},
        timeout_seconds=10.0,
    )

    assert len(findings) == 1
    assert findings[0].kind is FindingKind.URL_TIMEOUT


def test_validate_url_link_retries_get_after_head_exception() -> None:
    session = FakeSession()
    session._head_result = requests.ConnectionError("connection reset")
    session._get_result = FakeResponse(500)

    findings = validate_url_link(
        _make_link("https://example.com/error"),
        session=session,  # type: ignore[arg-type]
        url_cache={},
        timeout_seconds=10.0,
    )

    assert len(findings) == 1
    assert findings[0].kind is FindingKind.BROKEN_URL
    assert findings[0].status_code == 500


def test_validate_url_link_uses_cache_for_repeated_calls() -> None:
    session = FakeSession()
    url_cache: dict[str, list] = {}
    link = _make_link("https://example.com")

    first = validate_url_link(
        link,
        session=session,  # type: ignore[arg-type]
        url_cache=url_cache,
        timeout_seconds=10.0,
    )
    second = validate_url_link(
        link,
        session=session,  # type: ignore[arg-type]
        url_cache=url_cache,
        timeout_seconds=10.0,
    )

    assert first == []
    assert second == []
    assert session.calls == [("HEAD", "https://example.com", True, 10.0)]
