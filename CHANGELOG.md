# Changelog

## 1.1.2 - 2026-08-15

- fix Linux VPS installer permissions so the dedicated `wisp-mcp` service account can execute the installed virtual environment

## 1.1.1 - 2026-08-15

- report the installed package version from the MCP runtime and health endpoint

## 1.1.0 - 2026-08-15

- add a one-line hardened Linux VPS installer
- add guided OpenAI Secure MCP Tunnel setup
- add a copyable assistant onboarding prompt and VPS sizing guide
- support pytest 9 in development environments

## 1.0.0

- Generic Wisp Client API support.
- Local stdio and Streamable HTTP transports.
- Read-only server, file, audit, backup and database tools.
- Opt-in file, console, power, backup, database and server-setting operations.
- Separate destructive capability gate.
- Interactive setup and connection doctor.
