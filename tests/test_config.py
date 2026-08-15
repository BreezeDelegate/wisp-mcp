from __future__ import annotations

import pytest

from wisp_mcp.config import (
    WispError,
    env_bool,
    load_settings,
    safe_path,
    validate_object_id,
    validate_server_id,
)


def test_env_bool(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("FLAG", "true")
    assert env_bool("FLAG") is True
    monkeypatch.setenv("FLAG", "0")
    assert env_bool("FLAG") is False
    monkeypatch.setenv("FLAG", "maybe")
    with pytest.raises(WispError):
        env_bool("FLAG")


def test_panel_url_requires_https(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("WISP_PANEL_URL", "http://panel.example.test")
    with pytest.raises(WispError, match="HTTPS"):
        load_settings()


def test_remote_binding_fails_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("WISP_MCP_HOST", "0.0.0.0")
    monkeypatch.delenv("WISP_MCP_AUTH_TOKEN", raising=False)
    monkeypatch.delenv("WISP_ALLOW_UNAUTHENTICATED_REMOTE", raising=False)
    with pytest.raises(WispError, match="Remote MCP binding"):
        load_settings()


def test_remote_binding_requires_allowed_hosts(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("WISP_MCP_HOST", "0.0.0.0")
    monkeypatch.setenv("WISP_MCP_AUTH_TOKEN", "a" * 32)
    monkeypatch.delenv("WISP_MCP_ALLOWED_HOSTS", raising=False)
    with pytest.raises(WispError, match="ALLOWED_HOSTS"):
        load_settings()


def test_short_mcp_auth_token_is_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("WISP_MCP_AUTH_TOKEN", "too-short")
    with pytest.raises(WispError, match="at least 24"):
        load_settings()


@pytest.mark.parametrize("value", ["nope", "70000"])
def test_invalid_port_is_rejected(monkeypatch: pytest.MonkeyPatch, value: str) -> None:
    monkeypatch.setenv("WISP_MCP_PORT", value)
    with pytest.raises(WispError, match="WISP_MCP_PORT"):
        load_settings()


@pytest.mark.parametrize("value", ["nope", "0"])
def test_invalid_timeout_is_rejected(monkeypatch: pytest.MonkeyPatch, value: str) -> None:
    monkeypatch.setenv("WISP_TIMEOUT", value)
    with pytest.raises(WispError, match="WISP_TIMEOUT"):
        load_settings()


def test_safe_path_blocks_traversal() -> None:
    assert safe_path("/oxide/logs") == "/oxide/logs"
    for bad in ("oxide/logs", "/../etc/passwd", "/foo/./bar", "/foo\\bar"):
        with pytest.raises(WispError):
            safe_path(bad)


def test_server_id_validation() -> None:
    assert validate_server_id("e8a83c9b") == "e8a83c9b"
    with pytest.raises(WispError):
        validate_server_id("../bad")


def test_object_id_validation() -> None:
    assert validate_object_id("backup_123", "backup ID") == "backup_123"
    with pytest.raises(WispError, match="backup ID"):
        validate_object_id("../bad", "backup ID")


def test_new_write_capabilities_default_off(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("WISP_ALLOW_DATABASES", raising=False)
    monkeypatch.delenv("WISP_ALLOW_SERVER_SETTINGS", raising=False)
    settings = load_settings()
    assert settings.allow_databases is False
    assert settings.allow_server_settings is False
