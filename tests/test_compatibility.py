from __future__ import annotations

from typing import Any

import pytest

from wisp_mcp import compatibility
from wisp_mcp.config import WispError, load_settings


def _responses() -> dict[str, Any]:
    return {
        "/api/client/servers": {
            "object": "list",
            "data": [{"object": "server", "attributes": {"uuid_short": "abc12345", "name": "Demo"}}],
        },
        "/api/client/servers/abc12345": {
            "object": "server",
            "attributes": {"uuid_short": "abc12345", "name": "Demo"},
        },
        "/api/client/servers/abc12345/resources": {
            "status": "running",
            "process": {"cpu_used": 1.5, "memory_used": 1024, "disk_used": 2048},
        },
        "/api/client/servers/abc12345/files/directory": {"object": "list", "data": []},
        "/api/client/servers/abc12345/backups": {"object": "list", "data": []},
        "/api/client/servers/abc12345/databases": {"object": "list", "data": []},
    }


@pytest.mark.asyncio
async def test_live_contract_checks_core_routes(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("WISP_API_TOKEN", "test-token")
    monkeypatch.setenv("WISP_SERVER_ID", "abc12345")
    responses = _responses()
    calls: list[str] = []

    async def fake_request(self: Any, method: str, path: str, **kwargs: Any) -> Any:
        assert method == "GET"
        calls.append(path)
        return responses[path]

    monkeypatch.setattr(compatibility.WispClient, "request", fake_request)
    result = await compatibility.check_compatibility(load_settings())
    assert result.server_id == "abc12345"
    assert result.checks == ("servers", "details", "resources", "files", "backups", "databases")
    assert len(calls) == 6


@pytest.mark.asyncio
async def test_contract_rejects_silent_shape_change(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("WISP_API_TOKEN", "test-token")
    monkeypatch.setenv("WISP_SERVER_ID", "abc12345")
    responses = _responses()
    responses["/api/client/servers/abc12345/resources"] = {"state": "running", "process": {}}

    async def fake_request(self: Any, method: str, path: str, **kwargs: Any) -> Any:
        return responses[path]

    monkeypatch.setattr(compatibility.WispClient, "request", fake_request)
    with pytest.raises(WispError, match=r"resources\.status"):
        await compatibility.check_compatibility(load_settings())


@pytest.mark.asyncio
async def test_contract_without_default_server_only_checks_listing(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("WISP_API_TOKEN", "test-token")
    monkeypatch.delenv("WISP_SERVER_ID", raising=False)

    async def fake_request(self: Any, method: str, path: str, **kwargs: Any) -> Any:
        return {"object": "list", "data": []}

    monkeypatch.setattr(compatibility.WispClient, "request", fake_request)
    result = await compatibility.check_compatibility(load_settings())
    assert result.checks == ("servers",)
    assert result.server_id is None
