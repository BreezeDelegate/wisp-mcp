# Operations

## Safety model

Wisp MCP separates read-only access from changing and destructive operations.

A safe change sequence is:

1. Read server status and the relevant file or log.
2. Create a Wisp backup or copy the target file before a risky edit.
3. Make the smallest change needed.
4. Restart only when the application requires it.
5. Re-read the changed file and inspect status and recent logs.
6. Roll back if validation fails.

These rules are also sent to MCP clients as server instructions.

## Capability switches

| Variable | Enables |
| --- | --- |
| `WISP_ALLOW_COMMANDS` | Console commands |
| `WISP_ALLOW_FILE_WRITES` | Create, write, copy, rename, compress and extract files |
| `WISP_ALLOW_POWER` | Start, stop and restart |
| `WISP_ALLOW_BACKUPS` | Create, lock and restore backups |
| `WISP_ALLOW_DATABASES` | Create and modify databases |
| `WISP_ALLOW_SERVER_SETTINGS` | Monitoring, support access and panel update actions |
| `WISP_ALLOW_DESTRUCTIVE` | Delete, restore, rotate credentials, force kill and update actions |

Read-only tools do not require these switches.

## HTTP deployment

Use Streamable HTTP only when local stdio is not suitable. Put TLS in front of the service and set a long `WISP_MCP_AUTH_TOKEN`.

The server enables DNS rebinding protection. A remote bind also requires `WISP_MCP_ALLOWED_HOSTS`.

Do not expose port 8000 directly to the public Internet without an authenticated TLS layer.

## Upgrades

Before updating:

```bash
wisp-mcp doctor
pytest
```

After updating, run the same checks and verify the MCP client can list servers and read status.


## Large files and concurrent edits

Use `find_in_file` first when you know a symbol, setting, or error string. Use `read_file_chunk` only for the surrounding region you actually need. This keeps tool output bounded even for very large plugins and logs.

When editing an existing file, prefer `replace_in_file` for a focused change. It checks the SHA-256 fingerprint from the prior read before writing and verifies the resulting file afterward. Use `safe_write_file` when replacing the complete file is intentional. If the hash changed, re-read the file instead of forcing the write.

`write_file` remains available for creating a new file or for an intentional unguarded overwrite.

## Context quality policy

Context optimization is adaptive, not absolute. Use search and bounded reads to locate relevant code, then widen the read when correctness depends on global state, distant hooks, shared classes, control flow, or cross-file behavior. A full-file read is preferable to a token-saving shortcut when the shortcut increases regression risk.
