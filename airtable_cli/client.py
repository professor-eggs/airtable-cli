"""httpx wrapper with auth, rate limiting (token bucket), pagination, and error handling."""

from __future__ import annotations

import time
from collections.abc import Generator
from typing import Any, Optional

import httpx
from rich.console import Console

_console = Console(stderr=True)

BASE_URL_V0 = "https://api.airtable.com/v0"
BASE_URL_META = "https://api.airtable.com/v0/meta"
BASE_URL_BASES = "https://api.airtable.com/v0/bases"

MAX_RETRIES = 3
RATE_LIMIT = 5  # requests per second


class AirtableAPIError(Exception):
    def __init__(self, status_code: int, error_type: str, message: str) -> None:
        self.status_code = status_code
        self.error_type = error_type
        self.message = message
        super().__init__(f"[{status_code}] {error_type}: {message}")


class _TokenBucket:
    """Simple token bucket for rate limiting."""

    def __init__(self, rate: float) -> None:
        self.rate = rate
        self.tokens = rate
        self.last = time.monotonic()

    def consume(self) -> None:
        now = time.monotonic()
        elapsed = now - self.last
        self.tokens = min(self.rate, self.tokens + elapsed * self.rate)
        self.last = now
        if self.tokens < 1:
            sleep_time = (1 - self.tokens) / self.rate
            time.sleep(sleep_time)
            self.tokens = 0
        else:
            self.tokens -= 1


_bucket = _TokenBucket(RATE_LIMIT)


def _get_client(token: str) -> httpx.Client:
    return httpx.Client(
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        timeout=30.0,
    )


def _handle_response(response: httpx.Response) -> dict[str, Any]:
    if response.is_success:
        if response.content:
            return response.json()
        return {}
    try:
        body = response.json()
        err = body.get("error", {})
        error_type = err.get("type", "UNKNOWN_ERROR")
        message = err.get("message", response.text)
    except Exception:
        error_type = "UNKNOWN_ERROR"
        message = response.text
    raise AirtableAPIError(response.status_code, error_type, message)


def _request(
    method: str,
    url: str,
    token: str,
    *,
    params: Optional[dict] = None,
    json: Optional[dict | list] = None,
) -> dict[str, Any]:
    _bucket.consume()
    backoff = 1.0
    for attempt in range(MAX_RETRIES):
        with _get_client(token) as client:
            response = client.request(method, url, params=params, json=json)
        if response.status_code == 429:
            if attempt < MAX_RETRIES - 1:
                time.sleep(backoff)
                backoff *= 2
                continue
        return _handle_response(response)
    return _handle_response(response)  # type: ignore[reportPossiblyUnbound]


def get(url: str, token: str, params: Optional[dict] = None) -> dict[str, Any]:
    return _request("GET", url, token, params=params)


def post(url: str, token: str, json: dict | list) -> dict[str, Any]:
    return _request("POST", url, token, json=json)


def patch(url: str, token: str, json: dict | list) -> dict[str, Any]:
    return _request("PATCH", url, token, json=json)


def put(url: str, token: str, json: dict | list) -> dict[str, Any]:
    return _request("PUT", url, token, json=json)


def delete(url: str, token: str, params: Optional[dict] = None) -> dict[str, Any]:
    return _request("DELETE", url, token, params=params)


def paginate(
    url: str,
    token: str,
    params: Optional[dict] = None,
) -> Generator[dict[str, Any], None, None]:
    """Yield successive pages until no offset is returned."""
    params = dict(params or {})
    while True:
        data = get(url, token, params=params)
        yield data
        offset = data.get("offset")
        if not offset:
            break
        params["offset"] = offset
