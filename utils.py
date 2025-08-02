"""
utils.py – helpers for hen_client
"""
from __future__ import annotations

import re
from typing import Any, Dict, Iterable, Iterator, Mapping, Optional, Sequence, Tuple, TypeVar
from urllib.parse import urlencode, urljoin

try:
    # Optional (used only if configure_retries is called)
    from urllib3.util.retry import Retry  # type: ignore
    from requests.adapters import HTTPAdapter  # type: ignore
except Exception:  # pragma: no cover
    Retry = None  # type: ignore
    HTTPAdapter = None  # type: ignore


# The server sets a session cookie on /user/login.
# Name can vary; kept here if callers want to reference it.
SESSION_COOKIE_NAME = "JSESSIONID"


def build_url(base_url: str, path: str) -> str:
    """
    Join base_url and path robustly.
    Ensures a single slash between them and supports absolute/relative path inputs.
    """
    return urljoin(base_url.rstrip("/") + "/", path.lstrip("/"))


def merge_params(*mappings: Optional[Mapping[str, Any]]) -> Dict[str, Any]:
    """
    Merge multiple optional dictionaries into one, skipping keys with None values.
    Later mappings override earlier ones.
    """
    merged: Dict[str, Any] = {}
    for m in mappings:
        if not m:
            continue
        for k, v in m.items():
            if v is None:
                continue
            merged[k] = v
    return merged


def to_query(params: Mapping[str, Any]) -> str:
    """
    Encode query parameters using urllib.parse.urlencode, supporting sequences (doseq=True).
    """
    return urlencode(params, doseq=True)


def normalize_oid(value: Optional[str]) -> Optional[str]:
    """
    Some Aeneis deployments represent object IDs with a leading run of 'A' characters.
    This utility removes a leading 'A…' prefix if present. Safe no-op otherwise.

    Example:
        'AAAAa1b2c3' -> 'a1b2c3'
        '27b990ef-...' -> unchanged
    """
    if not value:
        return value
    return re.sub(r"^A+", "", value)


_T = TypeVar("_T")


def chunked(iterable: Iterable[_T], size: int) -> Iterator[Tuple[_T, ...]]:
    """
    Yield tuples of length <= size from an iterable. Useful for bulk endpoints.
    """
    if size <= 0:
        raise ValueError("size must be > 0")
    buf: Tuple[_T, ...] = tuple()
    for item in iterable:
        buf = (*buf, item)
        if len(buf) >= size:
            yield buf
            buf = tuple()
    if buf:
        yield buf


def configure_retries(
    session,
    *,
    total: int = 3,
    backoff_factor: float = 0.3,
    status_forcelist: Sequence[int] = (429, 500, 502, 503, 504),
    allowed_methods: Sequence[str] = ("GET", "PUT", "DELETE", "OPTIONS", "HEAD"),
) -> None:
    """
    Optionally attach a retry strategy to a requests.Session.
    Use in callers if you want resiliency against transient failures.

    Example:
        session = requests.Session()
        configure_retries(session)
    """
    if Retry is None or HTTPAdapter is None:  # pragma: no cover
        # urllib3 not importable in runtime; skip silently.
        return

    retry = Retry(
        total=total,
        read=total,
        connect=total,
        status=total,
        backoff_factor=backoff_factor,
        status_forcelist=frozenset(status_forcelist),
        allowed_methods=frozenset(m.upper() for m in allowed_methods),
        raise_on_status=False,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
