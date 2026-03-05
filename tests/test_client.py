"""Tests for the httpx client wrapper."""

import pytest
import httpx

from airtable_cli.client import AirtableAPIError, _handle_response, paginate


def _make_response(status_code: int, body: dict) -> httpx.Response:
    import json
    return httpx.Response(
        status_code=status_code,
        content=json.dumps(body).encode(),
        headers={"content-type": "application/json"},
    )


def test_handle_response_success():
    resp = _make_response(200, {"records": []})
    assert _handle_response(resp) == {"records": []}


def test_handle_response_error():
    resp = _make_response(422, {"error": {"type": "INVALID_REQUEST", "message": "bad input"}})
    with pytest.raises(AirtableAPIError) as exc_info:
        _handle_response(resp)
    err = exc_info.value
    assert err.status_code == 422
    assert err.error_type == "INVALID_REQUEST"
    assert "bad input" in err.message


def test_handle_response_404():
    resp = _make_response(404, {"error": {"type": "NOT_FOUND", "message": "Record not found"}})
    with pytest.raises(AirtableAPIError) as exc_info:
        _handle_response(resp)
    assert exc_info.value.status_code == 404


def test_api_error_str():
    err = AirtableAPIError(404, "NOT_FOUND", "Record not found")
    assert "404" in str(err)
    assert "NOT_FOUND" in str(err)
