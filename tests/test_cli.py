from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import pytest

from wisp_mcp import cli
from wisp_mcp.config import WispError


@pytest.mark.asyncio
async def test_doctor_checks_servers_and_default(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setenv("WISP_API_TOKEN", "test-token")
    monkeypatch.setenv("WISP_SERVER_ID", "abc12345")
    calls: list[str] = []

    async def fake_request(self: Any, method: str, path: str, **kwargs: Any) -> dict[str, Any]:
        calls.append(f"{method} {path}")
        return {"data": []}

    monkeypatch.setattr(cli.WispClient, "request", fake_request)
    await cli.doctor()
    assert calls == ["GET /api/client/servers", "GET /api/client/servers/abc12345/resources"]
    assert "Wisp API: OK" in capsys.readouterr().out


@pytest.mark.asyncio
async def test_doctor_requires_token(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("WISP_API_TOKEN", raising=False)
    with pytest.raises(WispError, match="WISP_API_TOKEN"):
        await cli.doctor()


def test_init_config_writes_private_file(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    answers = iter(["https://panel.example.test", "abc12345"])
    monkeypatch.setattr("builtins.input", lambda _prompt: next(answers))
    monkeypatch.setattr(cli.getpass, "getpass", lambda _prompt: "secret-token")
    target = tmp_path / "config.env"
    assert cli.init_config(target) == target
    text = target.read_text()
    assert "WISP_PANEL_URL=https://panel.example.test" in text
    assert "WISP_API_TOKEN=secret-token" in text
    assert target.stat().st_mode & 0o777 == 0o600


def test_main_defaults_to_stdio(monkeypatch: pytest.MonkeyPatch) -> None:
    called = False

    def fake_run() -> None:
        nonlocal called
        called = True

    monkeypatch.setattr(sys, "argv", ["wisp-mcp"])
    monkeypatch.setattr(cli, "run_stdio", fake_run)
    cli.main()
    assert called


def test_main_doctor_failure(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    async def fake_doctor() -> None:
        raise WispError("safe failure")

    monkeypatch.setattr(sys, "argv", ["wisp-mcp", "doctor"])
    monkeypatch.setattr(cli, "doctor", fake_doctor)
    with pytest.raises(SystemExit) as exc_info:
        cli.main()
    assert exc_info.value.code == 1
    assert "safe failure" in capsys.readouterr().err
