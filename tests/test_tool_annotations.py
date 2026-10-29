from __future__ import annotations

from wisp_mcp.server import mcp


def test_toggle_tools_are_not_marked_idempotent() -> None:
    tools = {tool.name: tool for tool in mcp._tool_manager.list_tools()}
    for name in ("toggle_monitoring", "toggle_support_access"):
        tool = tools[name]
        assert tool.annotations.read_only_hint is False
        assert tool.annotations.idempotent_hint is False
        assert tool.annotations.destructive_hint is True
