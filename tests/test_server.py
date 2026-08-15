from __future__ import annotations

from typing import Any

import pytest

from wisp_mcp.config import WispError, load_settings
from wisp_mcp.server import (
    _DESTRUCTIVE,
    _READ_ONLY,
    WispClient,
    _server_id,
    _truncate_file_payload,
    create_backup,
    list_servers,
    power,
    read_file,
    read_log_tail,
    send_console_command,
    server_status,
    write_file,
)


def test_tool_annotation_profiles() -> None:
    assert _READ_ONLY.read_only_hint is True
    assert _READ_ONLY.destructive_hint is False
    assert _DESTRUCTIVE.read_only_hint is False
    assert _DESTRUCTIVE.destructive_hint is True


def test_server_id_uses_default(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("WISP_SERVER_ID", "e8a83c9b")
    settings = load_settings()
    assert _server_id(settings, None) == "e8a83c9b"


def test_missing_default_server_id(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("WISP_SERVER_ID", raising=False)
    settings = load_settings()
    with pytest.raises(WispError, match="No server ID"):
        _server_id(settings, None)


def test_truncate_file_payload() -> None:
    payload = {"content": "abcdef"}
    result = _truncate_file_payload(payload, 3)
    assert result["content"] == "abc"
    assert result["truncated"] is True
    assert result["original_characters"] == 6


def test_small_file_payload_includes_hash_metadata() -> None:
    from hashlib import sha256

    payload = {"content": "abc"}
    result = _truncate_file_payload(payload, 3)
    assert result["content"] == "abc"
    assert result["truncated"] is False
    assert result["next_offset_chars"] is None
    assert result["sha256"] == sha256(b"abc").hexdigest()


def test_non_text_file_payload_is_unchanged() -> None:
    payload = {"content": 123}
    assert _truncate_file_payload(payload, 3) == payload


def test_mutating_capabilities_default_off(monkeypatch: pytest.MonkeyPatch) -> None:
    for key in (
        "WISP_ALLOW_COMMANDS",
        "WISP_ALLOW_FILE_WRITES",
        "WISP_ALLOW_POWER",
        "WISP_ALLOW_BACKUPS",
        "WISP_ALLOW_DESTRUCTIVE",
    ):
        monkeypatch.delenv(key, raising=False)
    settings = load_settings()
    assert settings.allow_commands is False
    assert settings.allow_file_writes is False
    assert settings.allow_power is False
    assert settings.allow_backups is False
    assert settings.allow_destructive is False


@pytest.mark.asyncio
async def test_list_servers_forwards_request(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("WISP_API_TOKEN", "test-token")
    calls: list[tuple[str, str]] = []

    async def fake_request(self: Any, method: str, path: str, **kwargs: Any) -> dict[str, Any]:
        calls.append((method, path))
        return {"data": []}

    monkeypatch.setattr(WispClient, "request", fake_request)
    assert await list_servers() == {"data": []}
    assert calls == [("GET", "/api/client/servers")]


@pytest.mark.asyncio
async def test_server_status_uses_default_server(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("WISP_API_TOKEN", "test-token")
    monkeypatch.setenv("WISP_SERVER_ID", "e8a83c9b")
    paths: list[str] = []

    async def fake_request(self: Any, method: str, path: str, **kwargs: Any) -> dict[str, Any]:
        paths.append(path)
        return {"status": 1}

    monkeypatch.setattr(WispClient, "request", fake_request)
    assert await server_status() == {"status": 1}
    assert paths == ["/api/client/servers/e8a83c9b/resources"]


@pytest.mark.asyncio
async def test_read_file_rejects_invalid_limit() -> None:
    with pytest.raises(WispError, match="max_chars"):
        await read_file("/server.log", max_chars=999)


@pytest.mark.asyncio
async def test_read_log_tail_returns_requested_lines(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("WISP_API_TOKEN", "test-token")
    monkeypatch.setenv("WISP_SERVER_ID", "e8a83c9b")

    async def fake_request(self: Any, method: str, path: str, **kwargs: Any) -> dict[str, Any]:
        return {"content": "one\ntwo\nthree\nfour"}

    monkeypatch.setattr(WispClient, "request", fake_request)
    result = await read_log_tail("/server.log", lines=2)
    assert result["content"] == "three\nfour"


@pytest.mark.asyncio
async def test_read_log_tail_rejects_non_text(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("WISP_API_TOKEN", "test-token")
    monkeypatch.setenv("WISP_SERVER_ID", "e8a83c9b")

    async def fake_request(self: Any, method: str, path: str, **kwargs: Any) -> dict[str, Any]:
        return {"content": 123}

    monkeypatch.setattr(WispClient, "request", fake_request)
    with pytest.raises(WispError, match="text file"):
        await read_log_tail("/server.log")


@pytest.mark.asyncio
async def test_write_file_requires_permission(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("WISP_SERVER_ID", "e8a83c9b")
    monkeypatch.delenv("WISP_ALLOW_FILE_WRITES", raising=False)
    with pytest.raises(WispError, match="ALLOW_FILE_WRITES"):
        await write_file("/test.txt", "hello")


@pytest.mark.asyncio
async def test_write_file_enforces_size_limit(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("WISP_SERVER_ID", "e8a83c9b")
    monkeypatch.setenv("WISP_ALLOW_FILE_WRITES", "true")
    monkeypatch.setenv("WISP_MAX_WRITE_BYTES", "1024")
    with pytest.raises(WispError, match="byte limit"):
        await write_file("/test.txt", "x" * 1025)


@pytest.mark.asyncio
async def test_console_command_requires_permission(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("WISP_SERVER_ID", "e8a83c9b")
    monkeypatch.delenv("WISP_ALLOW_COMMANDS", raising=False)
    with pytest.raises(WispError, match="ALLOW_COMMANDS"):
        await send_console_command("status")


@pytest.mark.asyncio
async def test_console_command_rejects_invalid_input(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("WISP_SERVER_ID", "e8a83c9b")
    monkeypatch.setenv("WISP_ALLOW_COMMANDS", "true")
    with pytest.raises(WispError, match="Invalid console command"):
        await send_console_command("\x00")


@pytest.mark.asyncio
async def test_force_kill_requires_destructive_permission(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("WISP_SERVER_ID", "e8a83c9b")
    monkeypatch.setenv("WISP_ALLOW_POWER", "true")
    monkeypatch.delenv("WISP_ALLOW_DESTRUCTIVE", raising=False)
    with pytest.raises(WispError, match="ALLOW_DESTRUCTIVE"):
        await power("kill")


@pytest.mark.asyncio
async def test_backup_name_validation(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("WISP_SERVER_ID", "e8a83c9b")
    monkeypatch.setenv("WISP_ALLOW_BACKUPS", "true")
    with pytest.raises(WispError, match="Invalid backup name"):
        await create_backup("   ")


@pytest.mark.asyncio
async def test_list_databases_forwards_include(monkeypatch: pytest.MonkeyPatch) -> None:
    from wisp_mcp.server import list_databases

    monkeypatch.setenv("WISP_API_TOKEN", "test-token")
    monkeypatch.setenv("WISP_SERVER_ID", "abc12345")
    calls: list[tuple[str, str, Any]] = []

    async def fake_request(self: Any, method: str, path: str, **kwargs: Any) -> dict[str, Any]:
        calls.append((method, path, kwargs.get("params")))
        return {"data": []}

    monkeypatch.setattr(WispClient, "request", fake_request)
    assert await list_databases() == {"data": []}
    assert calls == [
        (
            "GET",
            "/api/client/servers/abc12345/databases",
            {"page": 1, "per_page": 25, "include": "host"},
        )
    ]


@pytest.mark.asyncio
async def test_delete_database_requires_destructive(monkeypatch: pytest.MonkeyPatch) -> None:
    from wisp_mcp.server import delete_database

    monkeypatch.setenv("WISP_SERVER_ID", "abc12345")
    monkeypatch.setenv("WISP_ALLOW_DATABASES", "true")
    monkeypatch.delenv("WISP_ALLOW_DESTRUCTIVE", raising=False)
    with pytest.raises(WispError, match="WISP_ALLOW_DESTRUCTIVE"):
        await delete_database("db_1")


@pytest.mark.asyncio
async def test_server_settings_default_off(monkeypatch: pytest.MonkeyPatch) -> None:
    from wisp_mcp.server import toggle_monitoring

    monkeypatch.setenv("WISP_SERVER_ID", "abc12345")
    monkeypatch.delenv("WISP_ALLOW_SERVER_SETTINGS", raising=False)
    with pytest.raises(WispError, match="WISP_ALLOW_SERVER_SETTINGS"):
        await toggle_monitoring()


@pytest.mark.asyncio
async def test_list_servers_include(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("WISP_API_TOKEN", "test-token")
    calls: list[Any] = []

    async def fake_request(self: Any, method: str, path: str, **kwargs: Any) -> dict[str, Any]:
        calls.append((method, path, kwargs.get("params")))
        return {"data": []}

    monkeypatch.setattr(WispClient, "request", fake_request)
    assert await list_servers("node,allocations") == {"data": []}
    assert calls == [
        (
            "GET",
            "/api/client/servers",
            {"page": 1, "per_page": 25, "include": "node,allocations"},
        )
    ]


@pytest.mark.asyncio
async def test_list_servers_rejects_unknown_include() -> None:
    with pytest.raises(WispError, match="Unsupported include"):
        await list_servers("unknown")


@pytest.mark.asyncio
async def test_audit_logs_pagination(monkeypatch: pytest.MonkeyPatch) -> None:
    from wisp_mcp.server import audit_logs

    monkeypatch.setenv("WISP_API_TOKEN", "test-token")
    monkeypatch.setenv("WISP_SERVER_ID", "abc12345")
    calls: list[Any] = []

    async def fake_request(self: Any, method: str, path: str, **kwargs: Any) -> dict[str, Any]:
        calls.append((path, kwargs.get("params")))
        return {"data": []}

    monkeypatch.setattr(WispClient, "request", fake_request)
    await audit_logs(page=2, per_page=25)
    assert calls == [("/api/client/servers/abc12345/audit-logs", {"page": 2, "per_page": 25})]


@pytest.mark.asyncio
async def test_backup_helpers(monkeypatch: pytest.MonkeyPatch) -> None:
    from wisp_mcp.server import backup_download, lock_backup

    monkeypatch.setenv("WISP_API_TOKEN", "test-token")
    monkeypatch.setenv("WISP_SERVER_ID", "abc12345")
    monkeypatch.setenv("WISP_ALLOW_BACKUPS", "true")
    calls: list[tuple[str, str]] = []

    async def fake_request(self: Any, method: str, path: str, **kwargs: Any) -> dict[str, Any]:
        calls.append((method, path))
        return {"ok": True}

    monkeypatch.setattr(WispClient, "request", fake_request)
    await lock_backup("backup_1")
    await backup_download("backup_1")
    assert calls == [
        ("POST", "/api/client/servers/abc12345/backups/backup_1/locked"),
        ("GET", "/api/client/servers/abc12345/backups/backup_1/download"),
    ]


@pytest.mark.asyncio
async def test_create_database_forwards_payload(monkeypatch: pytest.MonkeyPatch) -> None:
    from wisp_mcp.server import create_database

    monkeypatch.setenv("WISP_API_TOKEN", "test-token")
    monkeypatch.setenv("WISP_SERVER_ID", "abc12345")
    monkeypatch.setenv("WISP_ALLOW_DATABASES", "true")
    calls: list[Any] = []

    async def fake_request(self: Any, method: str, path: str, **kwargs: Any) -> dict[str, Any]:
        calls.append((method, path, kwargs.get("json")))
        return {"ok": True}

    monkeypatch.setattr(WispClient, "request", fake_request)
    await create_database("game", "mysql-1", "%")
    assert calls == [
        (
            "POST",
            "/api/client/servers/abc12345/databases",
            {"name": "game", "host": "mysql-1", "connections_from": "%"},
        )
    ]


@pytest.mark.asyncio
async def test_rotate_database_password_route(monkeypatch: pytest.MonkeyPatch) -> None:
    from wisp_mcp.server import rotate_database_password

    monkeypatch.setenv("WISP_API_TOKEN", "test-token")
    monkeypatch.setenv("WISP_SERVER_ID", "abc12345")
    monkeypatch.setenv("WISP_ALLOW_DATABASES", "true")
    monkeypatch.setenv("WISP_ALLOW_DESTRUCTIVE", "true")
    paths: list[str] = []

    async def fake_request(self: Any, method: str, path: str, **kwargs: Any) -> dict[str, Any]:
        paths.append(path)
        return {"ok": True}

    monkeypatch.setattr(WispClient, "request", fake_request)
    await rotate_database_password("db_1")
    assert paths == ["/api/client/servers/abc12345/databases/db_1/rotate-password"]


@pytest.mark.asyncio
async def test_toggle_monitoring_route(monkeypatch: pytest.MonkeyPatch) -> None:
    from wisp_mcp.server import toggle_monitoring

    monkeypatch.setenv("WISP_API_TOKEN", "test-token")
    monkeypatch.setenv("WISP_SERVER_ID", "abc12345")
    monkeypatch.setenv("WISP_ALLOW_SERVER_SETTINGS", "true")
    paths: list[str] = []

    async def fake_request(self: Any, method: str, path: str, **kwargs: Any) -> dict[str, Any]:
        paths.append(path)
        return {"ok": True}

    monkeypatch.setattr(WispClient, "request", fake_request)
    await toggle_monitoring()
    assert paths == ["/api/client/servers/abc12345/advanced/monitor"]


@pytest.mark.asyncio
async def test_update_server_requires_both_gates(monkeypatch: pytest.MonkeyPatch) -> None:
    from wisp_mcp.server import update_server

    monkeypatch.setenv("WISP_SERVER_ID", "abc12345")
    monkeypatch.setenv("WISP_ALLOW_SERVER_SETTINGS", "true")
    monkeypatch.delenv("WISP_ALLOW_DESTRUCTIVE", raising=False)
    with pytest.raises(WispError, match="WISP_ALLOW_DESTRUCTIVE"):
        await update_server()


@pytest.mark.asyncio
async def test_list_directory_forwards_pagination(monkeypatch: pytest.MonkeyPatch) -> None:
    from wisp_mcp.server import list_directory

    monkeypatch.setenv("WISP_API_TOKEN", "test-token")
    monkeypatch.setenv("WISP_SERVER_ID", "abc12345")
    calls: list[tuple[Any, Any]] = []

    async def fake_request(self: Any, method: str, path: str, **kwargs: Any) -> dict[str, Any]:
        calls.append((kwargs.get("json"), kwargs.get("params")))
        return {"data": []}

    monkeypatch.setattr(WispClient, "request", fake_request)
    await list_directory("/oxide/plugins", page=2, per_page=10)
    assert calls == [({"path": "/oxide/plugins"}, {"page": 2, "per_page": 10})]


@pytest.mark.asyncio
async def test_read_file_chunk_returns_continuation_and_hash(monkeypatch: pytest.MonkeyPatch) -> None:
    from hashlib import sha256

    from wisp_mcp.server import read_file_chunk

    monkeypatch.setenv("WISP_API_TOKEN", "test-token")
    monkeypatch.setenv("WISP_SERVER_ID", "abc12345")
    content = "0123456789" * 300

    async def fake_request(self: Any, method: str, path: str, **kwargs: Any) -> dict[str, Any]:
        return {"content": content}

    monkeypatch.setattr(WispClient, "request", fake_request)
    result = await read_file_chunk("/plugin.cs", offset_chars=1000, max_chars=1000)
    assert result["content"] == content[1000:2000]
    assert result["next_offset_chars"] == 2000
    assert result["complete"] is False
    assert result["sha256"] == sha256(content.encode()).hexdigest()


@pytest.mark.asyncio
async def test_find_in_file_returns_small_line_numbered_context(monkeypatch: pytest.MonkeyPatch) -> None:
    from wisp_mcp.server import find_in_file

    monkeypatch.setenv("WISP_API_TOKEN", "test-token")
    monkeypatch.setenv("WISP_SERVER_ID", "abc12345")
    content = "one\nneedle here\nthree\nfour\n"

    async def fake_request(self: Any, method: str, path: str, **kwargs: Any) -> dict[str, Any]:
        return {"content": content}

    monkeypatch.setattr(WispClient, "request", fake_request)
    result = await find_in_file("/plugin.cs", "NEEDLE", context_lines=1)
    assert result["matches"][0]["line"] == 2
    assert "1: one" in result["matches"][0]["excerpt"]
    assert "2: needle here" in result["matches"][0]["excerpt"]


@pytest.mark.asyncio
async def test_safe_write_file_rejects_stale_hash_without_writing(monkeypatch: pytest.MonkeyPatch) -> None:
    from wisp_mcp.server import safe_write_file

    monkeypatch.setenv("WISP_API_TOKEN", "test-token")
    monkeypatch.setenv("WISP_SERVER_ID", "abc12345")
    monkeypatch.setenv("WISP_ALLOW_FILE_WRITES", "true")
    methods: list[str] = []

    async def fake_request(self: Any, method: str, path: str, **kwargs: Any) -> dict[str, Any]:
        methods.append(method)
        return {"content": "current"}

    monkeypatch.setattr(WispClient, "request", fake_request)
    with pytest.raises(WispError, match="File changed since it was read"):
        await safe_write_file("/config.json", "new", "0" * 64)
    assert methods == ["GET"]


@pytest.mark.asyncio
async def test_safe_write_file_verifies_written_content(monkeypatch: pytest.MonkeyPatch) -> None:
    from hashlib import sha256

    from wisp_mcp.server import safe_write_file

    monkeypatch.setenv("WISP_API_TOKEN", "test-token")
    monkeypatch.setenv("WISP_SERVER_ID", "abc12345")
    monkeypatch.setenv("WISP_ALLOW_FILE_WRITES", "true")
    before = "old"
    after = "new"
    responses = iter([{"content": before}, {"ok": True}, {"content": after}])

    async def fake_request(self: Any, method: str, path: str, **kwargs: Any) -> dict[str, Any]:
        return next(responses)

    monkeypatch.setattr(WispClient, "request", fake_request)
    result = await safe_write_file("/config.json", after, sha256(before.encode()).hexdigest())
    assert result["sha256"] == sha256(after.encode()).hexdigest()


@pytest.mark.asyncio
async def test_replace_in_file_changes_only_expected_match(monkeypatch: pytest.MonkeyPatch) -> None:
    from hashlib import sha256

    from wisp_mcp.server import replace_in_file

    monkeypatch.setenv("WISP_API_TOKEN", "test-token")
    monkeypatch.setenv("WISP_SERVER_ID", "abc12345")
    monkeypatch.setenv("WISP_ALLOW_FILE_WRITES", "true")
    before = "alpha\nbeta\ngamma\n"
    after = "alpha\nBETA\ngamma\n"
    written: list[str] = []
    reads = iter([before, after])

    async def fake_request(self: Any, method: str, path: str, **kwargs: Any) -> dict[str, Any]:
        if method == "GET":
            return {"content": next(reads)}
        written.append(kwargs["json"]["content"])
        return {"ok": True}

    monkeypatch.setattr(WispClient, "request", fake_request)
    result = await replace_in_file("/plugin.cs", "beta", "BETA", sha256(before.encode()).hexdigest())
    assert written == [after]
    assert result["replacements"] == 1
    assert result["sha256"] == sha256(after.encode()).hexdigest()


@pytest.mark.asyncio
async def test_list_servers_forwards_pagination_and_include(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("WISP_API_TOKEN", "test-token")
    calls: list[Any] = []

    async def fake_request(self: Any, method: str, path: str, **kwargs: Any) -> dict[str, Any]:
        calls.append(kwargs.get("params"))
        return {"data": []}

    monkeypatch.setattr(WispClient, "request", fake_request)
    await list_servers(include="node", page=2, per_page=10)
    assert calls == [{"page": 2, "per_page": 10, "include": "node"}]


@pytest.mark.asyncio
async def test_list_backups_forwards_pagination(monkeypatch: pytest.MonkeyPatch) -> None:
    from wisp_mcp.server import list_backups

    monkeypatch.setenv("WISP_API_TOKEN", "test-token")
    monkeypatch.setenv("WISP_SERVER_ID", "abc12345")
    calls: list[Any] = []

    async def fake_request(self: Any, method: str, path: str, **kwargs: Any) -> dict[str, Any]:
        calls.append(kwargs.get("params"))
        return {"data": []}

    monkeypatch.setattr(WispClient, "request", fake_request)
    await list_backups(page=3, per_page=5)
    assert calls == [{"page": 3, "per_page": 5}]
