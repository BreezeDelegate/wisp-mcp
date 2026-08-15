from __future__ import annotations

from typing import Any

import pytest

from wisp_mcp.config import load_settings
from wisp_mcp.server import BearerAuthMiddleware, create_http_app


async def _call_app(app: Any, path: str, authorization: str | None = None) -> tuple[int, bytes]:
    messages: list[dict[str, Any]] = []
    headers: list[tuple[bytes, bytes]] = []
    if authorization is not None:
        headers.append((b"authorization", authorization.encode()))
    scope = {
        "type": "http",
        "asgi": {"version": "3.0"},
        "http_version": "1.1",
        "method": "GET",
        "scheme": "http",
        "path": path,
        "raw_path": path.encode(),
        "query_string": b"",
        "headers": headers,
        "client": ("127.0.0.1", 12345),
        "server": ("127.0.0.1", 8000),
    }

    async def receive() -> dict[str, Any]:
        return {"type": "http.request", "body": b"", "more_body": False}

    async def send(message: dict[str, Any]) -> None:
        messages.append(message)

    await app(scope, receive, send)
    status = next(message["status"] for message in messages if message["type"] == "http.response.start")
    body = b"".join(
        message.get("body", b"") for message in messages if message["type"] == "http.response.body"
    )
    return status, body


def _downstream() -> Any:
    async def app(scope: Any, receive: Any, send: Any) -> None:
        await send({"type": "http.response.start", "status": 204, "headers": []})
        await send({"type": "http.response.body", "body": b""})

    return app


def test_create_http_app_local(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("WISP_MCP_HOST", "127.0.0.1")
    monkeypatch.delenv("WISP_MCP_AUTH_TOKEN", raising=False)
    assert create_http_app(load_settings()) is not None


@pytest.mark.asyncio
async def test_bearer_auth_rejects_missing_token() -> None:
    app = BearerAuthMiddleware(_downstream(), "a" * 32)
    status, body = await _call_app(app, "/mcp")
    assert status == 401
    assert b"unauthorized" in body


@pytest.mark.asyncio
async def test_bearer_auth_accepts_valid_token() -> None:
    token = "a" * 32
    app = BearerAuthMiddleware(_downstream(), token)
    status, _ = await _call_app(app, "/mcp", f"Bearer {token}")
    assert status == 204


@pytest.mark.asyncio
async def test_health_bypasses_bearer_auth() -> None:
    app = BearerAuthMiddleware(_downstream(), "a" * 32)
    status, _ = await _call_app(app, "/health")
    assert status == 204


@pytest.mark.asyncio
async def test_empty_auth_token_allows_local_mode() -> None:
    app = BearerAuthMiddleware(_downstream(), "")
    status, _ = await _call_app(app, "/mcp")
    assert status == 204
