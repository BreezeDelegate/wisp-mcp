# Changelog

## 1.2.2 - 2026-08-15

- ensure the OpenAI tunnel parent directory is owned by the Wisp service account before profile initialization
- use local WISP client/admin screenshots in the beginner recognition guide and README

## 1.2.1 - 2026-08-15

- make all public positioning and install examples hosting-provider agnostic
- add visual WISP panel recognition and beginner-focused GitHub Pages onboarding
- document ChatGPT, Claude Code, stdio, Streamable HTTP, and MCP Bundle client paths
- correct source-available terminology for the PolyForm Noncommercial license

## 1.2.0 - 2026-08-15

- add MCP Bundle distribution for one-click compatible clients
- add automated publication to the official MCP Registry with GitHub OIDC
- add an indexable GitHub Pages landing page, sitemap, and repository discovery metadata
- improve WISP Panel, game-server, Rust, and Minecraft discovery terms without tying the project to a hosting provider
- clarify the PolyForm Noncommercial license in the README

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
