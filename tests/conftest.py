from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
def base_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("WISP_PANEL_URL", "https://panel.example.test")
    monkeypatch.delenv("WISP_CONFIG_FILE", raising=False)
