from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .client import WispClient
from .config import Settings, WispError, validate_server_id


@dataclass(frozen=True)
class CompatibilityResult:
    checks: tuple[str, ...]
    server_id: str | None


def _mapping(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise WispError(f"Wisp compatibility check failed: {label} is not an object")
    return value


def _list(value: Any, label: str) -> list[Any]:
    if not isinstance(value, list):
        raise WispError(f"Wisp compatibility check failed: {label} is not a list")
    return value


def validate_servers(payload: Any) -> None:
    root = _mapping(payload, "servers response")
    data = _list(root.get("data"), "servers.data")
    if data:
        first = _mapping(data[0], "servers.data[0]")
        attrs = _mapping(first.get("attributes"), "servers.data[0].attributes")
        if not isinstance(attrs.get("name"), str):
            raise WispError("Wisp compatibility check failed: server name is missing")
        if not isinstance(attrs.get("uuid_short") or attrs.get("uuid"), str):
            raise WispError("Wisp compatibility check failed: server identifier is missing")


def validate_details(payload: Any) -> None:
    root = _mapping(payload, "server details response")
    attrs = _mapping(root.get("attributes"), "server details.attributes")
    if not isinstance(attrs.get("name"), str):
        raise WispError("Wisp compatibility check failed: details.name is missing")
    if not isinstance(attrs.get("uuid_short") or attrs.get("uuid"), str):
        raise WispError("Wisp compatibility check failed: details identifier is missing")


def validate_resources(payload: Any) -> None:
    root = _mapping(payload, "resources response")
    if not isinstance(root.get("status"), str):
        raise WispError("Wisp compatibility check failed: resources.status is missing")
    process = _mapping(root.get("process"), "resources.process")
    for key in ("cpu_used", "memory_used", "disk_used"):
        if not isinstance(process.get(key), int | float):
            raise WispError(f"Wisp compatibility check failed: resources.process.{key} is missing")


def validate_collection(payload: Any, label: str) -> None:
    root = _mapping(payload, f"{label} response")
    _list(root.get("data"), f"{label}.data")


async def check_compatibility(settings: Settings) -> CompatibilityResult:
    if not settings.api_token:
        raise WispError("WISP_API_TOKEN is not configured")

    client = WispClient(settings)
    checks: list[str] = []

    servers = await client.request("GET", "/api/client/servers")
    validate_servers(servers)
    checks.append("servers")

    if not settings.default_server_id:
        return CompatibilityResult(tuple(checks), None)

    sid = validate_server_id(settings.default_server_id)

    details = await client.request("GET", f"/api/client/servers/{sid}")
    validate_details(details)
    checks.append("details")

    resources = await client.request("GET", f"/api/client/servers/{sid}/resources")
    validate_resources(resources)
    checks.append("resources")

    files = await client.request("GET", f"/api/client/servers/{sid}/files/directory", json={"path": "/"})
    validate_collection(files, "files")
    checks.append("files")

    backups = await client.request("GET", f"/api/client/servers/{sid}/backups")
    validate_collection(backups, "backups")
    checks.append("backups")

    databases = await client.request("GET", f"/api/client/servers/{sid}/databases")
    validate_collection(databases, "databases")
    checks.append("databases")

    return CompatibilityResult(tuple(checks), sid)
