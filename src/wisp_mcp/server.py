from __future__ import annotations

import hashlib
import hmac
from typing import Annotated, Any, Literal

import uvicorn
from mcp.server import MCPServer
from mcp.server.transport_security import TransportSecuritySettings
from mcp.types import ToolAnnotations
from pydantic import Field
from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Receive, Scope, Send

from .client import APP_VERSION, WispClient
from .config import (
    Settings,
    WispError,
    load_settings,
    safe_path,
    validate_object_id,
    validate_server_id,
)

ServerIdArg = Annotated[
    str | None, Field(description="Wisp server ID. Omit to use the configured WISP_SERVER_ID default.")
]
PathArg = Annotated[str, Field(description="Path in the selected server filesystem, starting from its root.")]
PageArg = Annotated[int, Field(ge=1, description="1-based result page number.")]
PerPageArg = Annotated[
    int, Field(ge=1, le=25, description="Number of results to return per page, from 1 to 25.")
]
BackupIdArg = Annotated[str, Field(description="Backup object ID returned by list_backups.")]
DatabaseIdArg = Annotated[str, Field(description="Database object ID returned by list_databases.")]
Sha256Arg = Annotated[
    str, Field(description="64-character SHA-256 from the most recent read or fingerprint of the same file.")
]

_READ_ONLY = ToolAnnotations(
    read_only_hint=True,
    destructive_hint=False,
    idempotent_hint=True,
    open_world_hint=False,
)
_ADDITIVE = ToolAnnotations(
    read_only_hint=False,
    destructive_hint=False,
    idempotent_hint=False,
    open_world_hint=False,
)
_IDEMPOTENT_WRITE = ToolAnnotations(
    read_only_hint=False,
    destructive_hint=True,
    idempotent_hint=True,
    open_world_hint=False,
)
_DESTRUCTIVE = ToolAnnotations(
    read_only_hint=False,
    destructive_hint=True,
    idempotent_hint=False,
    open_world_hint=False,
)

mcp = MCPServer(
    "Wisp",
    version=APP_VERSION,
    instructions=(
        "Inspect before changing anything. Read the target file, server status, and relevant logs first. "
        "Before risky edits, create a Wisp backup or copy the file when those capabilities are enabled. "
        "For large files, use find_in_file and read_file_chunk to locate relevant areas first, "
        "but never trade correctness for token savings. Read the complete file when a change depends "
        "on global state, distant hooks, shared classes, control flow, or cross-file assumptions. "
        "For existing files, prefer replace_in_file or safe_write_file with the SHA-256 from a prior read. "
        "Optimize context only when it preserves confidence; spend more tokens when broader context "
        "reduces regression risk. Make the smallest useful change, restart only when required, then "
        "verify the file, status, and logs. "
        "Never expose API tokens or other secrets. Use destructive tools only for an explicit "
        "destructive request."
    ),
)


def _settings() -> Settings:
    return load_settings()


def _client() -> WispClient:
    return WispClient(_settings())


def _server_id(settings: Settings, server_id: str | None) -> str:
    value = (server_id or settings.default_server_id).strip()
    if not value:
        raise WispError("No server ID provided and WISP_SERVER_ID is not configured")
    return validate_server_id(value)


def _server_path(server_id: str, suffix: str = "") -> str:
    return f"/api/client/servers/{server_id}{suffix}"


def _require(enabled: bool, variable: str) -> None:
    if not enabled:
        raise WispError(f"Capability disabled. Set {variable}=true on the MCP host to enable it.")


def _include_params(value: str, allowed: set[str]) -> dict[str, str] | None:
    items = [item.strip() for item in value.split(",") if item.strip()]
    if not items:
        return None
    invalid = sorted(set(items) - allowed)
    if invalid:
        raise WispError(f"Unsupported include value: {', '.join(invalid)}")
    return {"include": ",".join(dict.fromkeys(items))}


def _page_params(page: int, per_page: int) -> dict[str, int]:
    if page < 1:
        raise WispError("page must be at least 1")
    if not 1 <= per_page <= 25:
        raise WispError("per_page must be between 1 and 25")
    return {"page": page, "per_page": per_page}


def _text_content(payload: Any) -> str:
    if not isinstance(payload, dict) or not isinstance(payload.get("content"), str):
        raise WispError("Wisp did not return text file content")
    return payload["content"]


def _sha256_text(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def _truncate_file_payload(payload: Any, max_chars: int) -> Any:
    if not isinstance(payload, dict) or not isinstance(payload.get("content"), str):
        return payload
    content = payload["content"]
    end = min(len(content), max_chars)
    return {
        **payload,
        "content": content[:end],
        "truncated": end < len(content),
        "original_characters": len(content),
        "returned_characters": end,
        "next_offset_chars": end if end < len(content) else None,
        "sha256": _sha256_text(content),
    }


@mcp.custom_route("/health", methods=["GET"])
async def health(_request: Any) -> JSONResponse:
    return JSONResponse({"status": "ok", "version": APP_VERSION})


@mcp.tool(annotations=_READ_ONLY)
async def capabilities() -> dict[str, Any]:
    """
    Inspect which Wisp operation classes are enabled before choosing a management tool. Returns
    configuration flags and the default server ID, but never API tokens or other secrets.
    """
    settings = _settings()
    return {
        "version": APP_VERSION,
        "panel": settings.panel_url,
        "default_server_id": settings.default_server_id or None,
        "commands": settings.allow_commands,
        "file_writes": settings.allow_file_writes,
        "power": settings.allow_power,
        "backups": settings.allow_backups,
        "databases": settings.allow_databases,
        "server_settings": settings.allow_server_settings,
        "destructive": settings.allow_destructive,
    }


@mcp.tool(annotations=_READ_ONLY)
async def list_servers(
    include: Annotated[
        str, Field(description="Comma-separated related resources: node, egg, allocations.")
    ] = "",
    page: PageArg = 1,
    per_page: PerPageArg = 25,
) -> Any:
    """
    List Wisp servers visible to the configured API token. Use this to discover server IDs; results
    are paginated and can optionally include node, egg, or allocation metadata.
    """
    params: dict[str, Any] = _page_params(page, per_page)
    include_params = _include_params(include, {"node", "egg", "allocations"})
    if include_params:
        params.update(include_params)
    return await _client().request("GET", "/api/client/servers", params=params)


@mcp.tool(annotations=_READ_ONLY)
async def server_details(
    server_id: ServerIdArg = None,
    include: Annotated[
        str, Field(description="Comma-separated related resources: node, egg, allocations, features.")
    ] = "",
) -> Any:
    """
    Read metadata for one Wisp server without changing it. Use for identity, allocation, feature,
    node, or egg details; omit server_id only when a default server is configured.
    """
    settings = _settings()
    sid = _server_id(settings, server_id)
    params = _include_params(include, {"node", "egg", "allocations", "features"})
    return await WispClient(settings).request("GET", _server_path(sid), params=params)


@mcp.tool(annotations=_READ_ONLY)
async def server_status(server_id: ServerIdArg = None) -> Any:
    """
    Read the current runtime state and resource usage for one server. Use for power state, CPU,
    memory, disk, network, and game-query checks; this performs no mutation.
    """
    settings = _settings()
    sid = _server_id(settings, server_id)
    return await WispClient(settings).request("GET", _server_path(sid, "/resources"))


@mcp.tool(annotations=_READ_ONLY)
async def audit_logs(server_id: ServerIdArg = None, page: PageArg = 1, per_page: PerPageArg = 20) -> Any:
    """
    Read one page of Wisp audit events for a server. Use to investigate recent panel actions or
    changes; page and per_page control pagination and no state is modified.
    """
    settings = _settings()
    sid = _server_id(settings, server_id)
    return await WispClient(settings).request(
        "GET", _server_path(sid, "/audit-logs"), params=_page_params(page, per_page)
    )


@mcp.tool(annotations=_READ_ONLY)
async def list_directory(
    path: PathArg = "/",
    page: PageArg = 1,
    per_page: PerPageArg = 25,
    server_id: ServerIdArg = None,
) -> Any:
    """
    List entries in one server directory without reading file contents. Use for filesystem discovery
    before read or write operations; results are paginated.
    """
    settings = _settings()
    sid = _server_id(settings, server_id)
    return await WispClient(settings).request(
        "GET",
        _server_path(sid, "/files/directory"),
        json={"path": safe_path(path)},
        params=_page_params(page, per_page),
    )


@mcp.tool(annotations=_READ_ONLY)
async def read_file(
    path: PathArg,
    server_id: ServerIdArg = None,
    max_chars: Annotated[
        int, Field(ge=1000, le=500000, description="Maximum file characters to return before truncation.")
    ] = 100_000,
) -> Any:
    """
    Read a text file and return its content plus fingerprint metadata. Use when the full file is
    needed; content is truncated at max_chars, so use read_file_chunk for controlled continuation.
    """
    if not 1_000 <= max_chars <= 500_000:
        raise WispError("max_chars must be between 1000 and 500000")
    settings = _settings()
    sid = _server_id(settings, server_id)
    payload = await WispClient(settings).request(
        "GET", _server_path(sid, "/files/read"), json={"path": safe_path(path)}
    )
    return _truncate_file_payload(payload, max_chars)


@mcp.tool(annotations=_READ_ONLY)
async def file_fingerprint(path: PathArg, server_id: ServerIdArg = None) -> dict[str, Any]:
    """
    Return SHA-256 and size metadata for a text file without returning its content. Use before
    safe_write_file or replace_in_file when only concurrency verification is needed.
    """
    settings = _settings()
    sid = _server_id(settings, server_id)
    clean_path = safe_path(path)
    payload = await WispClient(settings).request(
        "GET", _server_path(sid, "/files/read"), json={"path": clean_path}
    )
    content = _text_content(payload)
    return {
        "path": clean_path,
        "sha256": _sha256_text(content),
        "characters": len(content),
        "bytes": len(content.encode("utf-8")),
        "lines": len(content.splitlines()),
    }


@mcp.tool(annotations=_READ_ONLY)
async def read_file_chunk(
    path: PathArg,
    offset_chars: Annotated[
        int, Field(ge=0, description="Zero-based character offset where the chunk starts.")
    ] = 0,
    max_chars: Annotated[
        int, Field(ge=1000, le=100000, description="Maximum characters to return in this chunk.")
    ] = 40_000,
    server_id: ServerIdArg = None,
) -> dict[str, Any]:
    """
    Read a bounded character slice of a text file and return continuation metadata plus the
    whole-file SHA-256. Use for large files when full context is unnecessary; continue with
    next_offset_chars.
    """
    if offset_chars < 0:
        raise WispError("offset_chars must be at least 0")
    if not 1_000 <= max_chars <= 100_000:
        raise WispError("max_chars must be between 1000 and 100000")
    settings = _settings()
    sid = _server_id(settings, server_id)
    clean_path = safe_path(path)
    payload = await WispClient(settings).request(
        "GET", _server_path(sid, "/files/read"), json={"path": clean_path}
    )
    content = _text_content(payload)
    total = len(content)
    if offset_chars > total:
        raise WispError("offset_chars is beyond the end of the file")
    end = min(offset_chars + max_chars, total)
    return {
        "path": clean_path,
        "content": content[offset_chars:end],
        "offset_chars": offset_chars,
        "returned_characters": end - offset_chars,
        "total_characters": total,
        "next_offset_chars": end if end < total else None,
        "complete": end >= total,
        "sha256": _sha256_text(content),
    }


@mcp.tool(annotations=_READ_ONLY)
async def find_in_file(
    path: PathArg,
    query: Annotated[
        str,
        Field(
            min_length=1,
            max_length=500,
            description="Literal text to find; regular expressions are not supported.",
        ),
    ],
    max_matches: Annotated[int, Field(ge=1, le=20, description="Maximum matching excerpts to return.")] = 20,
    context_lines: Annotated[
        int, Field(ge=0, le=10, description="Lines of context to include before and after each match.")
    ] = 3,
    case_sensitive: Annotated[
        bool, Field(description="Whether query matching should preserve letter case.")
    ] = False,
    server_id: ServerIdArg = None,
) -> dict[str, Any]:
    """
    Find literal text in a server file and return bounded, line-numbered excerpts. Use to locate
    relevant sections before chunked reading or exact replacement; this is not regex search and
    makes no changes.
    """
    if not query or len(query) > 500:
        raise WispError("query must contain between 1 and 500 characters")
    if not 1 <= max_matches <= 20:
        raise WispError("max_matches must be between 1 and 20")
    if not 0 <= context_lines <= 10:
        raise WispError("context_lines must be between 0 and 10")
    settings = _settings()
    sid = _server_id(settings, server_id)
    clean_path = safe_path(path)
    payload = await WispClient(settings).request(
        "GET", _server_path(sid, "/files/read"), json={"path": clean_path}
    )
    content = _text_content(payload)
    raw_lines = content.splitlines(keepends=True)
    lines = [line.rstrip("\r\n") for line in raw_lines]
    needle = query if case_sensitive else query.casefold()
    matches: list[dict[str, Any]] = []
    char_cursor = 0
    for index, line in enumerate(lines):
        haystack = line if case_sensitive else line.casefold()
        if needle in haystack:
            start = max(0, index - context_lines)
            stop = min(len(lines), index + context_lines + 1)
            excerpt = "\n".join(f"{i + 1}: {lines[i]}" for i in range(start, stop))
            excerpt_truncated = len(excerpt) > 4_000
            if excerpt_truncated:
                excerpt = excerpt[:4_000] + "…"
            matches.append(
                {
                    "line": index + 1,
                    "char_offset": char_cursor + haystack.find(needle),
                    "excerpt": excerpt,
                    "excerpt_truncated": excerpt_truncated,
                }
            )
            if len(matches) >= max_matches:
                break
        char_cursor += len(raw_lines[index])
    return {
        "path": clean_path,
        "query": query,
        "matches": matches,
        "match_count_returned": len(matches),
        "limited": len(matches) >= max_matches,
        "sha256": _sha256_text(content),
        "total_characters": len(content),
        "total_lines": len(lines),
    }


@mcp.tool(annotations=_READ_ONLY)
async def read_log_tail(
    path: PathArg,
    lines: Annotated[
        int, Field(ge=1, le=2000, description="Number of lines to return from the end of the log.")
    ] = 200,
    server_id: ServerIdArg = None,
) -> dict[str, Any]:
    """
    Return the last requested lines from a text log file. Use for recent diagnostics after commands,
    power actions, or edits; it reads the file without modifying it.
    """
    if not 1 <= lines <= 2000:
        raise WispError("lines must be between 1 and 2000")
    settings = _settings()
    sid = _server_id(settings, server_id)
    payload = await WispClient(settings).request(
        "GET", _server_path(sid, "/files/read"), json={"path": safe_path(path)}
    )
    if not isinstance(payload, dict) or not isinstance(payload.get("content"), str):
        raise WispError("Wisp did not return text file content")
    content = payload["content"]
    tail = "\n".join(content.splitlines()[-lines:])
    return {"path": safe_path(path), "lines": lines, "content": tail}


@mcp.tool(annotations=_ADDITIVE)
async def create_directory(path: PathArg, server_id: ServerIdArg = None) -> Any:
    """
    Create a directory in the server filesystem. Use only when a new directory is required; this
    mutates filesystem state and requires WISP_ALLOW_FILE_WRITES.
    """
    settings = _settings()
    _require(settings.allow_file_writes, "WISP_ALLOW_FILE_WRITES")
    sid = _server_id(settings, server_id)
    return await WispClient(settings).request(
        "POST", _server_path(sid, "/files/directory"), json={"path": safe_path(path)}
    )


@mcp.tool(annotations=_IDEMPOTENT_WRITE)
async def write_file(
    path: PathArg,
    content: Annotated[str, Field(description="Complete UTF-8 text content to create or overwrite.")],
    server_id: ServerIdArg = None,
) -> Any:
    """
    Create or fully overwrite a text file. Use for new files or deliberate full replacement; it
    mutates filesystem state, requires WISP_ALLOW_FILE_WRITES, and does not protect against
    concurrent edits.
    """
    settings = _settings()
    _require(settings.allow_file_writes, "WISP_ALLOW_FILE_WRITES")
    if len(content.encode("utf-8")) > settings.max_write_bytes:
        raise WispError(f"write_file exceeds the {settings.max_write_bytes} byte limit")
    sid = _server_id(settings, server_id)
    return await WispClient(settings).request(
        "POST",
        _server_path(sid, "/files/write"),
        json={"path": safe_path(path), "content": content},
    )


@mcp.tool(annotations=_IDEMPOTENT_WRITE)
async def safe_write_file(
    path: PathArg,
    content: Annotated[str, Field(description="Complete replacement UTF-8 text content.")],
    expected_sha256: Sha256Arg,
    server_id: ServerIdArg = None,
) -> dict[str, Any]:
    """
    Overwrite an existing text file only when its current SHA-256 matches expected_sha256, then
    verify the stored result. Prefer this over write_file for existing files; requires
    WISP_ALLOW_FILE_WRITES.
    """
    settings = _settings()
    _require(settings.allow_file_writes, "WISP_ALLOW_FILE_WRITES")
    if len(content.encode("utf-8")) > settings.max_write_bytes:
        raise WispError(f"safe_write_file exceeds the {settings.max_write_bytes} byte limit")
    expected = expected_sha256.strip().lower()
    if len(expected) != 64 or any(ch not in "0123456789abcdef" for ch in expected):
        raise WispError("expected_sha256 must be a 64-character hexadecimal SHA-256")
    sid = _server_id(settings, server_id)
    clean_path = safe_path(path)
    client = WispClient(settings)
    before = _text_content(
        await client.request("GET", _server_path(sid, "/files/read"), json={"path": clean_path})
    )
    before_sha = _sha256_text(before)
    if not hmac.compare_digest(before_sha, expected):
        raise WispError(
            f"File changed since it was read: expected SHA-256 {expected}, current {before_sha}. "
            "Re-read before writing."
        )
    await client.request(
        "POST", _server_path(sid, "/files/write"), json={"path": clean_path, "content": content}
    )
    after = _text_content(
        await client.request("GET", _server_path(sid, "/files/read"), json={"path": clean_path})
    )
    after_sha = _sha256_text(after)
    intended_sha = _sha256_text(content)
    if not hmac.compare_digest(after_sha, intended_sha):
        raise WispError("Wisp write verification failed: stored content does not match the requested content")
    return {
        "ok": True,
        "path": clean_path,
        "previous_sha256": before_sha,
        "sha256": after_sha,
        "bytes": len(after.encode("utf-8")),
    }


@mcp.tool(annotations=_IDEMPOTENT_WRITE)
async def replace_in_file(
    path: PathArg,
    old: Annotated[str, Field(min_length=1, description="Exact existing text to replace.")],
    new: Annotated[str, Field(description="Replacement text.")],
    expected_sha256: Sha256Arg,
    expected_count: Annotated[
        int, Field(ge=1, le=100, description="Exact number of old-text matches required before editing.")
    ] = 1,
    server_id: ServerIdArg = None,
) -> dict[str, Any]:
    """
    Replace an exact text snippet only when the file SHA-256 and match count are exactly as
    expected, then verify the result. Prefer for small edits to existing files; requires
    WISP_ALLOW_FILE_WRITES.
    """
    if not old:
        raise WispError("old must not be empty")
    if not 1 <= expected_count <= 100:
        raise WispError("expected_count must be between 1 and 100")
    settings = _settings()
    _require(settings.allow_file_writes, "WISP_ALLOW_FILE_WRITES")
    expected = expected_sha256.strip().lower()
    if len(expected) != 64 or any(ch not in "0123456789abcdef" for ch in expected):
        raise WispError("expected_sha256 must be a 64-character hexadecimal SHA-256")
    sid = _server_id(settings, server_id)
    clean_path = safe_path(path)
    client = WispClient(settings)
    before = _text_content(
        await client.request("GET", _server_path(sid, "/files/read"), json={"path": clean_path})
    )
    before_sha = _sha256_text(before)
    if not hmac.compare_digest(before_sha, expected):
        raise WispError(
            f"File changed since it was read: expected SHA-256 {expected}, current {before_sha}. "
            "Re-read before editing."
        )
    actual_count = before.count(old)
    if actual_count != expected_count:
        raise WispError(
            f"Expected {expected_count} exact match(es), found {actual_count}; no change was made"
        )
    updated = before.replace(old, new, expected_count)
    if len(updated.encode("utf-8")) > settings.max_write_bytes:
        raise WispError(f"replace_in_file exceeds the {settings.max_write_bytes} byte limit")
    await client.request(
        "POST", _server_path(sid, "/files/write"), json={"path": clean_path, "content": updated}
    )
    after = _text_content(
        await client.request("GET", _server_path(sid, "/files/read"), json={"path": clean_path})
    )
    after_sha = _sha256_text(after)
    intended_sha = _sha256_text(updated)
    if not hmac.compare_digest(after_sha, intended_sha):
        raise WispError("Wisp edit verification failed: stored content does not match the intended content")
    return {
        "ok": True,
        "path": clean_path,
        "replacements": expected_count,
        "previous_sha256": before_sha,
        "sha256": after_sha,
        "bytes": len(after.encode("utf-8")),
    }


@mcp.tool(annotations=_ADDITIVE)
async def copy_file(path: PathArg, server_id: ServerIdArg = None) -> Any:
    """
    Ask Wisp to copy a file in place. Use to create a safety copy before risky edits when supported
    by the panel; this writes filesystem state and requires WISP_ALLOW_FILE_WRITES.
    """
    settings = _settings()
    _require(settings.allow_file_writes, "WISP_ALLOW_FILE_WRITES")
    sid = _server_id(settings, server_id)
    return await WispClient(settings).request(
        "POST", _server_path(sid, "/files/copy"), json={"path": safe_path(path)}
    )


@mcp.tool(annotations=_DESTRUCTIVE)
async def rename_file(
    path: PathArg,
    to: Annotated[str, Field(description="Destination path or new name in the selected server filesystem.")],
    server_id: ServerIdArg = None,
) -> Any:
    """
    Rename or move a server file to a new path. Use only when the existing path should change; this
    mutates filesystem state and requires WISP_ALLOW_FILE_WRITES.
    """
    settings = _settings()
    _require(settings.allow_file_writes, "WISP_ALLOW_FILE_WRITES")
    sid = _server_id(settings, server_id)
    return await WispClient(settings).request(
        "PUT",
        _server_path(sid, "/files/rename"),
        json={"path": safe_path(path), "to": safe_path(to)},
    )


@mcp.tool(annotations=_ADDITIVE)
async def compress_files(
    paths: Annotated[
        list[str],
        Field(
            min_length=1, max_length=100, description="Server file or directory paths to add to the archive."
        ),
    ],
    to: Annotated[str, Field(description="Destination directory for the generated archive.")] = "/",
    server_id: ServerIdArg = None,
) -> Any:
    """
    Create an archive from up to 100 server paths. Use for packaging or pre-change snapshots; this
    creates a new filesystem object and requires WISP_ALLOW_FILE_WRITES.
    """
    settings = _settings()
    _require(settings.allow_file_writes, "WISP_ALLOW_FILE_WRITES")
    if not paths or len(paths) > 100:
        raise WispError("paths must contain between 1 and 100 entries")
    sid = _server_id(settings, server_id)
    return await WispClient(settings).request(
        "POST",
        _server_path(sid, "/files/compress"),
        json={"paths": [safe_path(path) for path in paths], "to": safe_path(to)},
    )


@mcp.tool(annotations=_DESTRUCTIVE)
async def decompress_archive(path: PathArg, server_id: ServerIdArg = None) -> Any:
    """
    Extract an archive in the server filesystem. Use only when archive contents should be written to
    disk; existing paths may be affected and WISP_ALLOW_FILE_WRITES is required.
    """
    settings = _settings()
    _require(settings.allow_file_writes, "WISP_ALLOW_FILE_WRITES")
    sid = _server_id(settings, server_id)
    return await WispClient(settings).request(
        "POST", _server_path(sid, "/files/decompress"), json={"path": safe_path(path)}
    )


@mcp.tool(annotations=_DESTRUCTIVE)
async def delete_file(path: PathArg, server_id: ServerIdArg = None) -> Any:
    """
    Permanently delete a server file. Use only for an explicit deletion request; this is destructive
    and requires both WISP_ALLOW_FILE_WRITES and WISP_ALLOW_DESTRUCTIVE.
    """
    settings = _settings()
    _require(settings.allow_file_writes, "WISP_ALLOW_FILE_WRITES")
    _require(settings.allow_destructive, "WISP_ALLOW_DESTRUCTIVE")
    sid = _server_id(settings, server_id)
    return await WispClient(settings).request(
        "DELETE", _server_path(sid, "/files/delete"), json={"path": safe_path(path)}
    )


@mcp.tool(annotations=_DESTRUCTIVE)
async def send_console_command(
    command: Annotated[
        str,
        Field(
            min_length=1, max_length=4096, description="Single command to execute in the game-server console."
        ),
    ],
    server_id: ServerIdArg = None,
) -> Any:
    """
    Execute one command in the game-server console. Use for explicit runtime administration
    commands; effects depend on the command and WISP_ALLOW_COMMANDS must be enabled.
    """
    settings = _settings()
    _require(settings.allow_commands, "WISP_ALLOW_COMMANDS")
    command = command.strip()
    if not command or len(command) > 4096 or "\x00" in command or "\r" in command:
        raise WispError("Invalid console command")
    sid = _server_id(settings, server_id)
    return await WispClient(settings).request(
        "POST", _server_path(sid, "/command"), json={"command": command}
    )


@mcp.tool(annotations=_DESTRUCTIVE)
async def power(
    signal: Annotated[
        Literal["start", "stop", "restart", "kill"],
        Field(description="Power action; kill is a forced stop and requires destructive access."),
    ],
    server_id: ServerIdArg = None,
) -> Any:
    """
    Change a server power state with start, stop, restart, or force-kill. Use only when a power
    action is intended; WISP_ALLOW_POWER is required and kill also requires WISP_ALLOW_DESTRUCTIVE.
    """
    settings = _settings()
    _require(settings.allow_power, "WISP_ALLOW_POWER")
    if signal == "kill":
        _require(settings.allow_destructive, "WISP_ALLOW_DESTRUCTIVE")
    sid = _server_id(settings, server_id)
    return await WispClient(settings).request("POST", _server_path(sid, "/power"), json={"signal": signal})


@mcp.tool(annotations=_READ_ONLY)
async def list_backups(server_id: ServerIdArg = None, page: PageArg = 1, per_page: PerPageArg = 25) -> Any:
    """
    List one page of backups for a server without modifying them. Use to discover backup IDs, names,
    state, and metadata before restore, delete, lock, or download operations.
    """
    settings = _settings()
    sid = _server_id(settings, server_id)
    return await WispClient(settings).request(
        "GET", _server_path(sid, "/backups"), params=_page_params(page, per_page)
    )


@mcp.tool(annotations=_ADDITIVE)
async def create_backup(
    name: Annotated[
        str, Field(min_length=1, max_length=120, description="Human-readable name for the new backup.")
    ],
    server_id: ServerIdArg = None,
) -> Any:
    """
    Create a named server backup. Use before risky changes or when a new recovery point is required;
    this creates panel state and requires WISP_ALLOW_BACKUPS.
    """
    settings = _settings()
    _require(settings.allow_backups, "WISP_ALLOW_BACKUPS")
    name = name.strip()
    if not name or len(name) > 120 or "\x00" in name:
        raise WispError("Invalid backup name")
    sid = _server_id(settings, server_id)
    return await WispClient(settings).request("POST", _server_path(sid, "/backups"), json={"name": name})


@mcp.tool(annotations=_DESTRUCTIVE)
async def deploy_backup(backup_id: BackupIdArg, server_id: ServerIdArg = None) -> Any:
    """
    Restore a server from an existing backup ID. Use only for an explicit restore request because
    current server data can be replaced; requires WISP_ALLOW_BACKUPS and WISP_ALLOW_DESTRUCTIVE.
    """
    settings = _settings()
    _require(settings.allow_backups, "WISP_ALLOW_BACKUPS")
    _require(settings.allow_destructive, "WISP_ALLOW_DESTRUCTIVE")
    sid = _server_id(settings, server_id)
    bid = validate_object_id(backup_id, "backup ID")
    return await WispClient(settings).request("POST", _server_path(sid, f"/backups/{bid}/deploy"))


@mcp.tool(annotations=_DESTRUCTIVE)
async def delete_backup(backup_id: BackupIdArg, server_id: ServerIdArg = None) -> Any:
    """
    Permanently delete a backup by ID. Use only for an explicit backup deletion request; requires
    WISP_ALLOW_BACKUPS and WISP_ALLOW_DESTRUCTIVE.
    """
    settings = _settings()
    _require(settings.allow_backups, "WISP_ALLOW_BACKUPS")
    _require(settings.allow_destructive, "WISP_ALLOW_DESTRUCTIVE")
    sid = _server_id(settings, server_id)
    bid = validate_object_id(backup_id, "backup ID")
    return await WispClient(settings).request("DELETE", _server_path(sid, f"/backups/{bid}"))


@mcp.tool(annotations=_ADDITIVE)
async def lock_backup(backup_id: BackupIdArg, server_id: ServerIdArg = None) -> Any:
    """
    Change the panel lock state for a backup ID. Use to protect a backup from accidental deletion
    when supported; requires WISP_ALLOW_BACKUPS and mutates backup state.
    """
    settings = _settings()
    _require(settings.allow_backups, "WISP_ALLOW_BACKUPS")
    sid = _server_id(settings, server_id)
    bid = validate_object_id(backup_id, "backup ID")
    return await WispClient(settings).request("POST", _server_path(sid, f"/backups/{bid}/locked"))


@mcp.tool(annotations=_READ_ONLY)
async def backup_download(backup_id: BackupIdArg, server_id: ServerIdArg = None) -> Any:
    """
    Request Wisp download metadata for a backup without changing it. Use when a client needs the
    panel-provided backup download response for an existing backup ID.
    """
    settings = _settings()
    sid = _server_id(settings, server_id)
    bid = validate_object_id(backup_id, "backup ID")
    return await WispClient(settings).request("GET", _server_path(sid, f"/backups/{bid}/download"))


@mcp.tool(annotations=_READ_ONLY)
async def list_databases(
    server_id: ServerIdArg = None,
    include_host: Annotated[
        bool, Field(description="Include related database host metadata in each result.")
    ] = True,
    page: PageArg = 1,
    per_page: PerPageArg = 25,
) -> Any:
    """
    List one page of databases attached to a server. Use to discover database IDs and optionally
    host metadata; this is read-only and page/per_page control pagination.
    """
    settings = _settings()
    sid = _server_id(settings, server_id)
    params: dict[str, Any] = _page_params(page, per_page)
    if include_host:
        params["include"] = "host"
    return await WispClient(settings).request("GET", _server_path(sid, "/databases"), params=params)


@mcp.tool(annotations=_ADDITIVE)
async def create_database(
    name: Annotated[
        str, Field(min_length=1, max_length=64, description="Database name requested from Wisp.")
    ],
    host: Annotated[
        str, Field(min_length=1, max_length=128, description="Wisp database host identifier to allocate on.")
    ],
    connections_from: Annotated[
        str, Field(description="Allowed client host pattern; % allows connections from any host.")
    ] = "%",
    server_id: ServerIdArg = None,
) -> Any:
    """
    Create a database allocation for a server through the Wisp Client API. Use only when a new
    database is requested; this changes panel state and requires WISP_ALLOW_DATABASES.
    """
    settings = _settings()
    _require(settings.allow_databases, "WISP_ALLOW_DATABASES")
    name = name.strip()
    host = host.strip()
    connections_from = connections_from.strip()
    if not name or len(name) > 64 or not host or len(host) > 128 or not connections_from:
        raise WispError("Invalid database parameters")
    sid = _server_id(settings, server_id)
    return await WispClient(settings).request(
        "POST",
        _server_path(sid, "/databases"),
        json={"name": name, "host": host, "connections_from": connections_from},
    )


@mcp.tool(annotations=_DESTRUCTIVE)
async def rotate_database_password(database_id: DatabaseIdArg, server_id: ServerIdArg = None) -> Any:
    """
    Generate a new password for an existing database. Use only for an explicit credential rotation
    because the old password stops working; requires WISP_ALLOW_DATABASES and
    WISP_ALLOW_DESTRUCTIVE.
    """
    settings = _settings()
    _require(settings.allow_databases, "WISP_ALLOW_DATABASES")
    _require(settings.allow_destructive, "WISP_ALLOW_DESTRUCTIVE")
    sid = _server_id(settings, server_id)
    did = validate_object_id(database_id, "database ID")
    return await WispClient(settings).request("POST", _server_path(sid, f"/databases/{did}/rotate-password"))


@mcp.tool(annotations=_DESTRUCTIVE)
async def delete_database(database_id: DatabaseIdArg, server_id: ServerIdArg = None) -> Any:
    """
    Permanently delete a database allocation by ID. Use only for an explicit deletion request; this
    is destructive and requires WISP_ALLOW_DATABASES and WISP_ALLOW_DESTRUCTIVE.
    """
    settings = _settings()
    _require(settings.allow_databases, "WISP_ALLOW_DATABASES")
    _require(settings.allow_destructive, "WISP_ALLOW_DESTRUCTIVE")
    sid = _server_id(settings, server_id)
    did = validate_object_id(database_id, "database ID")
    return await WispClient(settings).request("DELETE", _server_path(sid, f"/databases/{did}"))


@mcp.tool(annotations=_IDEMPOTENT_WRITE)
async def toggle_monitoring(server_id: ServerIdArg = None) -> Any:
    """
    Toggle Wisp monitoring for the selected server. Use only when the monitoring state should
    change; this mutates server settings and requires WISP_ALLOW_SERVER_SETTINGS.
    """
    settings = _settings()
    _require(settings.allow_server_settings, "WISP_ALLOW_SERVER_SETTINGS")
    sid = _server_id(settings, server_id)
    return await WispClient(settings).request("POST", _server_path(sid, "/advanced/monitor"))


@mcp.tool(annotations=_IDEMPOTENT_WRITE)
async def toggle_support_access(server_id: ServerIdArg = None) -> Any:
    """
    Toggle hosting-provider support access for the selected server. Use only when support access
    should change; this mutates server settings and requires WISP_ALLOW_SERVER_SETTINGS.
    """
    settings = _settings()
    _require(settings.allow_server_settings, "WISP_ALLOW_SERVER_SETTINGS")
    sid = _server_id(settings, server_id)
    return await WispClient(settings).request("POST", _server_path(sid, "/advanced/support"))


@mcp.tool(annotations=_DESTRUCTIVE)
async def update_server(
    beta: Annotated[
        bool, Field(description="Request the beta update channel instead of the stable channel.")
    ] = False,
    server_id: ServerIdArg = None,
) -> Any:
    """
    Run the Wisp egg update action for the selected server, optionally using the beta channel. Use
    only for an explicit update request; this can change server files/runtime and requires
    server-settings plus destructive access.
    """
    settings = _settings()
    _require(settings.allow_server_settings, "WISP_ALLOW_SERVER_SETTINGS")
    _require(settings.allow_destructive, "WISP_ALLOW_DESTRUCTIVE")
    sid = _server_id(settings, server_id)
    return await WispClient(settings).request(
        "POST", _server_path(sid, "/advanced/update"), json={"beta": beta}
    )


class BearerAuthMiddleware:
    """Small pure-ASGI bearer guard; avoids BaseHTTPMiddleware streaming pitfalls."""

    def __init__(self, app: ASGIApp, token: str) -> None:
        self.app = app
        self.token = token

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http" or scope.get("path") == "/health" or not self.token:
            await self.app(scope, receive, send)
            return

        headers = {key.lower(): value for key, value in scope.get("headers", [])}
        raw = headers.get(b"authorization", b"")
        expected = f"Bearer {self.token}".encode()
        if not hmac.compare_digest(raw, expected):
            response = JSONResponse(
                {"error": "unauthorized"},
                status_code=401,
                headers={"WWW-Authenticate": "Bearer"},
            )
            await response(scope, receive, send)
            return
        await self.app(scope, receive, send)


def create_http_app(settings: Settings | None = None) -> ASGIApp:
    settings = settings or _settings()
    security = TransportSecuritySettings(
        enable_dns_rebinding_protection=True,
        allowed_hosts=list(settings.mcp_allowed_hosts),
        allowed_origins=list(settings.mcp_allowed_origins),
    )
    app = mcp.streamable_http_app(
        host=settings.mcp_host,
        json_response=True,
        stateless_http=True,
        transport_security=security,
    )
    return BearerAuthMiddleware(app, settings.mcp_auth_token)


def run_stdio() -> None:
    mcp.run()


def run_http() -> None:
    settings = _settings()
    uvicorn.run(
        create_http_app(settings),
        host=settings.mcp_host,
        port=settings.mcp_port,
        log_level="info",
        proxy_headers=False,
        server_header=False,
    )


if __name__ == "__main__":
    run_http()
