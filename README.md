# Wisp MCP — game server management for Wisp Panel

Wisp MCP is an open-source Model Context Protocol (MCP) server for the **Wisp game panel Client API**. It lets MCP-compatible clients inspect and manage Wisp-hosted game servers: status, files, console commands, power, backups, databases, audit logs, and common panel operations.

It is provider-agnostic. If your game host exposes the standard Wisp Client API, the same MCP can work with it. **VeryCloud** is documented as a tested provider example.

[![CI](https://github.com/BreezeDelegate/wisp-mcp/actions/workflows/ci.yml/badge.svg)](https://github.com/BreezeDelegate/wisp-mcp/actions/workflows/ci.yml)
[![Release](https://img.shields.io/github/v/release/BreezeDelegate/wisp-mcp)](https://github.com/BreezeDelegate/wisp-mcp/releases/latest)
[![Python](https://img.shields.io/badge/python-3.11%2B-blue)](https://www.python.org/)
[![MCP Registry](https://img.shields.io/badge/MCP_Registry-active-2ea44f)](https://registry.modelcontextprotocol.io/?q=io.github.BreezeDelegate%2Fwisp-mcp)

**Links:** [documentation](https://breezedelegate.github.io/wisp-mcp/) · [official MCP Registry](https://registry.modelcontextprotocol.io/?q=io.github.BreezeDelegate%2Fwisp-mcp) · [latest release](https://github.com/BreezeDelegate/wisp-mcp/releases/latest)

## What Wisp MCP can do

- list Wisp servers and inspect live CPU, memory, disk, network, and state;
- browse and read server files and log tails;
- edit, create, rename, compress, decompress, and delete files when explicitly enabled;
- send console commands and control server power;
- create, list, lock, download, restore, and delete backups;
- list and manage panel databases;
- inspect audit logs and common Wisp monitoring/support state;
- run locally over stdio or remotely over Streamable HTTP;
- keep changing and destructive operations disabled by default.

Because Wisp MCP targets the panel rather than a particular game, it can be used with **Rust, Minecraft, and other game servers hosted through Wisp**.

## Supported panels and hosts

### Wisp Panel

Any compatible Wisp installation can be configured with its panel URL and a Wisp Client API token:

```env
WISP_PANEL_URL=https://panel.example.com
WISP_API_TOKEN=your_token
```

### VeryCloud

VeryCloud game servers use Wisp. Use:

```env
WISP_PANEL_URL=https://panel.verycloud.fr
```

Then create a Client API token from your Wisp account. See [VeryCloud setup](docs/verycloud.md).

## Start here

### One-line Linux VPS install

For Debian 12 or Ubuntu 24.04+:

```bash
curl -fsSL https://raw.githubusercontent.com/BreezeDelegate/wisp-mcp/main/install-vps.sh | sudo bash -s -- --with-openai
```

The installer creates a dedicated service account, stores Wisp credentials outside the repository, verifies the Wisp API, and can install the official OpenAI secure tunnel client. Credentials are entered directly in the terminal and are not passed on the command line.

### Local quick start

Requirements: Python 3.11 or newer and a Wisp Client API token.

```bash
git clone https://github.com/BreezeDelegate/wisp-mcp.git
cd wisp-mcp
./setup.sh
```

For an existing Python environment:

```bash
python -m pip install .
wisp-mcp init
wisp-mcp doctor
wisp-mcp
```

`wisp-mcp` uses stdio by default. `wisp-mcp serve` exposes Streamable HTTP for remote deployments.

### MCP Bundle

Releases from v1.2.0 also include a `.mcpb` bundle for MCP clients that support the MCP Bundle format. The bundle collects the panel URL, API token, optional default server ID, and capability switches through the client UI instead of requiring manual environment-file editing.

## AI-guided setup

If you want an assistant to guide the entire setup, copy this prompt:

```text
Help me install Wisp MCP from https://github.com/BreezeDelegate/wisp-mcp and connect it to my MCP client. Read the current repository docs first and reply in my language. Guide me one step at a time and do as much of the technical work as possible. Never ask me to paste API tokens, passwords, private keys, or tunnel runtime keys into chat; tell me where to enter secrets directly in the terminal or provider UI. If I need an always-on machine, help me choose the smallest sensible Linux VPS for my real workload and do not oversell hardware. Verify Wisp with doctor before continuing. Start read-only; if I want management, enable only the capabilities I need and keep destructive operations disabled unless I explicitly request them. For later server changes, inspect first, back up risky files, make the smallest change, test it, check logs, and never claim success without verification.
```

See the longer [AI-guided setup](docs/ai-guided-setup.md), [VPS sizing](docs/vps.md), and [operations guide](docs/operations.md).

## Configuration

The default local configuration file is:

```text
~/.config/wisp-mcp/config.env
```

Required values:

```env
WISP_PANEL_URL=https://panel.example.com
WISP_API_TOKEN=your_token
```

`WISP_SERVER_ID` is optional. When set, tools can omit `server_id`.

Changing operations are opt-in:

```env
WISP_ALLOW_COMMANDS=true
WISP_ALLOW_FILE_WRITES=true
WISP_ALLOW_POWER=true
WISP_ALLOW_BACKUPS=true
WISP_ALLOW_DATABASES=false
WISP_ALLOW_SERVER_SETTINGS=false
WISP_ALLOW_DESTRUCTIVE=false
```

Keep `WISP_ALLOW_DESTRUCTIVE=false` for normal administration. Deleting files or backups, restoring backups, rotating database passwords, deleting databases, force-killing a server, and running panel update actions require the separate destructive gate.

## Remote HTTP

Keep the listener on loopback unless a reverse proxy or private tunnel needs a remote bind.

```env
WISP_MCP_HOST=0.0.0.0
WISP_MCP_PORT=8000
WISP_MCP_AUTH_TOKEN=use_a_long_random_value
WISP_MCP_ALLOWED_HOSTS=mcp.example.com
WISP_MCP_ALLOWED_ORIGINS=https://mcp.example.com
```

Run:

```bash
wisp-mcp serve
```

The MCP endpoint is `/mcp`; health is `/health`.

## Docker

```bash
cp .env.example .env
# edit .env
docker compose up -d --build
```

The example compose publishes the service on localhost only.

## Security model

API and MCP tokens are never returned by tools. Remote HTTP fails closed unless authentication is configured. File paths and object IDs are validated, write size is limited, and server-changing capabilities are opt-in.

The MCP server publishes operating instructions to clients: inspect first, back up before risky changes, make the smallest change, and verify status and logs afterward.

Report security issues privately as described in [SECURITY.md](SECURITY.md).

## Documentation

- [Getting started](docs/getting-started.md)
- [VeryCloud Wisp MCP setup](docs/verycloud.md)
- [VPS sizing](docs/vps.md)
- [Operations and security](docs/operations.md)
- [ChatGPT / OpenAI tunnel](docs/chatgpt.md)
- [AI-guided setup](docs/ai-guided-setup.md)

## FAQ

### Is this a Wisp Panel MCP server?

Yes. Wisp MCP exposes the Wisp Client API as Model Context Protocol tools.

### Does it work with VeryCloud?

Yes. VeryCloud is a documented Wisp provider. Configure `https://panel.verycloud.fr` and a Wisp Client API token.

### Is it tied to Rust or Minecraft?

No. It manages the Wisp server container through the panel API, so the same integration can be used for Rust, Minecraft, and other games hosted in Wisp.

### Can it modify my game server?

Only when you enable the relevant capability. Read-only access is the default and destructive operations have a separate switch.

## License

Wisp MCP is distributed under the [PolyForm Noncommercial License 1.0.0](LICENSE). Commercial licensing requires separate permission from the copyright holder.
