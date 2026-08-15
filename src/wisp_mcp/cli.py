from __future__ import annotations

import argparse
import asyncio
import getpass
import sys
from pathlib import Path

from .client import WispClient
from .compatibility import check_compatibility
from .config import WispError, default_config_path, load_settings, validate_server_id
from .server import run_http, run_stdio


def _write_config(path: Path, values: dict[str, str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(f"{key}={value}\n" for key, value in values.items()), encoding="utf-8")
    path.chmod(0o600)


def init_config(path: Path | None = None) -> Path:
    target = path or default_config_path()
    panel = input("Wisp panel URL: ").strip().rstrip("/")
    server_id = input("Default server ID (optional): ").strip()
    token = getpass.getpass("Wisp API token: ").strip()
    if not panel or not token:
        raise WispError("Panel URL and API token are required")
    if server_id:
        validate_server_id(server_id)
    values = {
        "WISP_PANEL_URL": panel,
        "WISP_API_TOKEN": token,
        "WISP_SERVER_ID": server_id,
        "WISP_ALLOW_COMMANDS": "false",
        "WISP_ALLOW_FILE_WRITES": "false",
        "WISP_ALLOW_POWER": "false",
        "WISP_ALLOW_BACKUPS": "false",
        "WISP_ALLOW_DATABASES": "false",
        "WISP_ALLOW_SERVER_SETTINGS": "false",
        "WISP_ALLOW_DESTRUCTIVE": "false",
    }
    _write_config(target, values)
    return target


async def compatibility() -> None:
    settings = load_settings()
    result = await check_compatibility(settings)
    suffix = f" | default: {result.server_id}" if result.server_id else ""
    print(f"Wisp compatibility: OK | checks: {len(result.checks)}{suffix}")


async def doctor() -> None:
    settings = load_settings()
    if not settings.api_token:
        raise WispError("WISP_API_TOKEN is not configured")
    client = WispClient(settings)
    payload = await client.request("GET", "/api/client/servers")
    count = len(payload.get("data", [])) if isinstance(payload, dict) else 0
    if settings.default_server_id:
        sid = validate_server_id(settings.default_server_id)
        await client.request("GET", f"/api/client/servers/{sid}/resources")
        print(f"Wisp API: OK | servers: {count} | default: {sid}")
    else:
        print(f"Wisp API: OK | servers: {count}")


def main() -> None:
    parser = argparse.ArgumentParser(prog="wisp-mcp")
    sub = parser.add_subparsers(dest="command")
    sub.add_parser("stdio", help="run the MCP server over stdio")
    sub.add_parser("serve", help="run the MCP server over Streamable HTTP")
    sub.add_parser("doctor", help="validate configuration and Wisp API access")
    sub.add_parser("compatibility", help="run read-only live Wisp API contract checks")
    init_parser = sub.add_parser("init", help="create a local configuration file")
    init_parser.add_argument("--path", type=Path)
    sub.add_parser("config-path", help="print the default configuration path")
    args = parser.parse_args()

    try:
        if args.command in {None, "stdio"}:
            run_stdio()
        elif args.command == "serve":
            run_http()
        elif args.command == "doctor":
            asyncio.run(doctor())
        elif args.command == "compatibility":
            asyncio.run(compatibility())
        elif args.command == "init":
            path = init_config(args.path)
            print(f"Configuration written to {path}")
        elif args.command == "config-path":
            print(default_config_path())
    except WispError as exc:
        print(f"wisp-mcp: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()
