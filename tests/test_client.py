from __future__ import annotations

import httpx
import pytest

from wisp_mcp import client as client_module
from wisp_mcp.client import WispClient, _redact
from wisp_mcp.config import WispError, load_settings


def test_redact_nested_secrets() -> None:
    payload = {
        "token": "abc",
        "nested": {"password": "secret", "message": "safe"},
        "items": [{"session": "cookie"}],
    }
    redacted = _redact(payload)
    assert redacted["token"] == "[redacted]"
    assert redacted["nested"]["password"] == "[redacted]"
    assert redacted["nested"]["message"] == "safe"
    assert redacted["items"][0]["session"] == "[redacted]"


def test_redact_truncates_long_strings() -> None:
    redacted = _redact("x" * 700)
    assert isinstance(redacted, str)
    assert len(redacted) < 700
    assert redacted.endswith("…")


def test_headers_require_api_token(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("WISP_API_TOKEN", raising=False)
    client = WispClient(load_settings())
    with pytest.raises(WispError, match="API_TOKEN"):
        client._headers()


@pytest.mark.asyncio
async def test_request_timeout_is_sanitized(monkeypatch: pytest.MonkeyPatch) -> None:
    token = "super-secret-token-value"
    monkeypatch.setenv("WISP_API_TOKEN", token)
    client = WispClient(load_settings())

    async def boom(*args: object, **kwargs: object) -> httpx.Response:
        raise httpx.ConnectTimeout(f"contains {token}")

    monkeypatch.setattr(httpx.AsyncClient, "request", boom)

    with pytest.raises(WispError) as exc_info:
        await client.request("GET", "/api/client/servers")

    message = str(exc_info.value)
    assert token not in message
    assert "timed out" in message


@pytest.mark.asyncio
async def test_request_network_error_is_sanitized(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("WISP_API_TOKEN", "test-token")
    client = WispClient(load_settings())

    async def boom(*args: object, **kwargs: object) -> httpx.Response:
        request = httpx.Request("GET", "https://panel.example.com/api/client/servers")
        raise httpx.ConnectError("network down", request=request)

    monkeypatch.setattr(httpx.AsyncClient, "request", boom)

    with pytest.raises(WispError, match="Could not reach"):
        await client.request("GET", "/api/client/servers")


@pytest.mark.asyncio
async def test_request_retries_then_handles_no_content(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("WISP_API_TOKEN", "test-token")
    client = WispClient(load_settings())
    calls = 0
    sleeps: list[float] = []

    async def fake_request(*args: object, **kwargs: object) -> httpx.Response:
        nonlocal calls
        calls += 1
        if calls == 1:
            return httpx.Response(503, headers={"Retry-After": "0"})
        return httpx.Response(204)

    async def fake_sleep(delay: float) -> None:
        sleeps.append(delay)

    monkeypatch.setattr(httpx.AsyncClient, "request", fake_request)
    monkeypatch.setattr(client_module.asyncio, "sleep", fake_sleep)

    result = await client.request("POST", "/api/client/servers/abc/power", json={"signal": "start"})
    assert result == {"ok": True, "status_code": 204}
    assert calls == 2
    assert sleeps == [0.1]


@pytest.mark.asyncio
async def test_request_retries_with_invalid_retry_after(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("WISP_API_TOKEN", "test-token")
    client = WispClient(load_settings())
    calls = 0
    sleeps: list[float] = []

    async def fake_request(*args: object, **kwargs: object) -> httpx.Response:
        nonlocal calls
        calls += 1
        if calls == 1:
            return httpx.Response(429, headers={"Retry-After": "invalid"})
        request = httpx.Request("GET", "https://panel.example.com/api/client/servers")
        return httpx.Response(200, request=request, json={"ok": True})

    async def fake_sleep(delay: float) -> None:
        sleeps.append(delay)

    monkeypatch.setattr(httpx.AsyncClient, "request", fake_request)
    monkeypatch.setattr(client_module.asyncio, "sleep", fake_sleep)

    result = await client.request("GET", "/api/client/servers")
    assert result == {"ok": True}
    assert calls == 2
    assert sleeps == [0.25]


@pytest.mark.asyncio
async def test_http_error_redacts_sensitive_fields(monkeypatch: pytest.MonkeyPatch) -> None:
    token = "upstream-api-token-value"
    monkeypatch.setenv("WISP_API_TOKEN", token)
    client = WispClient(load_settings())

    async def fake_request(*args: object, **kwargs: object) -> httpx.Response:
        request = httpx.Request("GET", "https://panel.example.com/api/client/servers")
        return httpx.Response(
            401,
            request=request,
            json={"token": "leak", "error": f"upstream echoed {token}"},
        )

    monkeypatch.setattr(httpx.AsyncClient, "request", fake_request)

    with pytest.raises(WispError) as exc_info:
        await client.request("GET", "/api/client/servers")

    message = str(exc_info.value)
    assert "leak" not in message
    assert token not in message
    assert "[redacted]" in message
    assert "401" in message


@pytest.mark.asyncio
async def test_non_json_http_error_is_safe(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("WISP_API_TOKEN", "test-token")
    client = WispClient(load_settings())

    async def fake_request(*args: object, **kwargs: object) -> httpx.Response:
        request = httpx.Request("GET", "https://panel.example.com/api/client/servers")
        return httpx.Response(500, request=request, text="upstream exploded")

    monkeypatch.setattr(httpx.AsyncClient, "request", fake_request)

    with pytest.raises(WispError) as exc_info:
        await client.request("GET", "/api/client/servers")

    assert "500" in str(exc_info.value)
    assert "upstream exploded" in str(exc_info.value)
