from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse

from dotenv import load_dotenv

_ID_RE = re.compile(r"^[A-Za-z0-9_-]{1,64}$")


class WispError(RuntimeError):
    pass


def default_config_path() -> Path:
    return Path.home() / ".config" / "wisp-mcp" / "config.env"


def _load_env_files() -> None:
    explicit = os.getenv("WISP_CONFIG_FILE", "").strip()
    if explicit:
        load_dotenv(Path(explicit).expanduser(), override=False)
    else:
        path = default_config_path()
        if path.is_file():
            load_dotenv(path, override=False)
    load_dotenv(override=False)


def env_bool(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    value = raw.strip().lower()
    if value in {"1", "true", "yes", "on"}:
        return True
    if value in {"0", "false", "no", "off", ""}:
        return False
    raise WispError(f"{name} must be true or false")


def _csv(name: str) -> tuple[str, ...]:
    return tuple(item.strip() for item in os.getenv(name, "").split(",") if item.strip())


def _int(name: str, default: int, minimum: int, maximum: int) -> int:
    raw = os.getenv(name, str(default)).strip()
    try:
        value = int(raw)
    except ValueError as exc:
        raise WispError(f"{name} must be an integer") from exc
    if not minimum <= value <= maximum:
        raise WispError(f"{name} must be between {minimum} and {maximum}")
    return value


def _float(name: str, default: float, minimum: float, maximum: float) -> float:
    raw = os.getenv(name, str(default)).strip()
    try:
        value = float(raw)
    except ValueError as exc:
        raise WispError(f"{name} must be a number") from exc
    if not minimum <= value <= maximum:
        raise WispError(f"{name} must be between {minimum:g} and {maximum:g}")
    return value


@dataclass(frozen=True, slots=True)
class Settings:
    panel_url: str
    api_token: str
    default_server_id: str
    timeout: float
    max_write_bytes: int
    allow_commands: bool
    allow_file_writes: bool
    allow_power: bool
    allow_backups: bool
    allow_databases: bool
    allow_server_settings: bool
    allow_destructive: bool
    mcp_host: str
    mcp_port: int
    mcp_auth_token: str
    mcp_allowed_hosts: tuple[str, ...]
    mcp_allowed_origins: tuple[str, ...]
    allow_unauthenticated_remote: bool


def load_settings() -> Settings:
    _load_env_files()
    panel_url = os.getenv("WISP_PANEL_URL", "").strip().rstrip("/")
    if not panel_url:
        raise WispError("WISP_PANEL_URL is not configured")
    parsed = urlparse(panel_url)
    if (
        parsed.scheme != "https"
        or not parsed.netloc
        or parsed.username
        or parsed.password
        or parsed.query
        or parsed.fragment
        or parsed.path not in {"", "/"}
    ):
        raise WispError(
            "WISP_PANEL_URL must be an HTTPS origin without credentials, path, query, or fragment"
        )

    mcp_host = os.getenv("WISP_MCP_HOST", "127.0.0.1").strip() or "127.0.0.1"
    mcp_auth_token = os.getenv("WISP_MCP_AUTH_TOKEN", "").strip()
    allow_unauthenticated_remote = env_bool("WISP_ALLOW_UNAUTHENTICATED_REMOTE")
    is_loopback = mcp_host in {"127.0.0.1", "localhost", "::1"}
    if not is_loopback and not mcp_auth_token and not allow_unauthenticated_remote:
        raise WispError(
            "Remote MCP binding requires WISP_MCP_AUTH_TOKEN or WISP_ALLOW_UNAUTHENTICATED_REMOTE=true"
        )
    if mcp_auth_token and len(mcp_auth_token) < 24:
        raise WispError("WISP_MCP_AUTH_TOKEN must be at least 24 characters")

    allowed_hosts = _csv("WISP_MCP_ALLOWED_HOSTS")
    if not allowed_hosts:
        if is_loopback:
            allowed_hosts = ("127.0.0.1:*", "localhost:*", "[::1]:*")
        else:
            raise WispError("WISP_MCP_ALLOWED_HOSTS is required when binding MCP remotely")

    return Settings(
        panel_url=panel_url,
        api_token=os.getenv("WISP_API_TOKEN", "").strip(),
        default_server_id=os.getenv("WISP_SERVER_ID", "").strip(),
        timeout=_float("WISP_TIMEOUT", 30, 1, 120),
        max_write_bytes=_int("WISP_MAX_WRITE_BYTES", 2_000_000, 1_024, 10_000_000),
        allow_commands=env_bool("WISP_ALLOW_COMMANDS"),
        allow_file_writes=env_bool("WISP_ALLOW_FILE_WRITES"),
        allow_power=env_bool("WISP_ALLOW_POWER"),
        allow_backups=env_bool("WISP_ALLOW_BACKUPS"),
        allow_databases=env_bool("WISP_ALLOW_DATABASES"),
        allow_server_settings=env_bool("WISP_ALLOW_SERVER_SETTINGS"),
        allow_destructive=env_bool("WISP_ALLOW_DESTRUCTIVE"),
        mcp_host=mcp_host,
        mcp_port=_int("WISP_MCP_PORT", 8000, 1, 65535),
        mcp_auth_token=mcp_auth_token,
        mcp_allowed_hosts=allowed_hosts,
        mcp_allowed_origins=_csv("WISP_MCP_ALLOWED_ORIGINS"),
        allow_unauthenticated_remote=allow_unauthenticated_remote,
    )


def validate_server_id(value: str) -> str:
    value = value.strip()
    if not _ID_RE.fullmatch(value):
        raise WispError("Invalid server ID")
    return value


def validate_object_id(value: str, label: str = "ID") -> str:
    value = value.strip()
    if not _ID_RE.fullmatch(value):
        raise WispError(f"Invalid {label}")
    return value


def safe_path(path: str) -> str:
    if not isinstance(path, str) or not path.startswith("/"):
        raise WispError("Server file paths must start with '/'")
    if len(path) > 4096 or "\x00" in path or "\\" in path:
        raise WispError("Invalid server file path")
    if any(part in {"..", "."} for part in path.split("/")):
        raise WispError("Server file paths cannot contain '.' or '..' segments")
    return path
