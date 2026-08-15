# Wisp MCP

Wisp MCP exposes the Wisp game panel Client API through Model Context Protocol.

It is designed for day-to-day server administration: inspect status and logs, edit files, send console commands, control power, manage backups, and handle common database or panel operations without giving the MCP process unrestricted host access.

## Start here

If you want an assistant to guide the entire setup, copy the ready-made prompt in [docs/ai-guided-setup.md](docs/ai-guided-setup.md). It is written for people who do not want to learn server administration first.

Copy this into your assistant:

```text
Help me install Wisp MCP from https://github.com/BreezeDelegate/wisp-mcp and connect it to my AI client. Read the current repository docs first and reply in my language. Guide me one step at a time and do as much of the technical work as possible. Never ask me to paste API tokens, passwords, private keys, or tunnel runtime keys into chat; tell me where to enter secrets directly in the terminal or provider UI. If I need an always-on machine, help me choose the smallest sensible Linux VPS for my real workload and do not oversell hardware. For ChatGPT/OpenAI on Debian 12 or Ubuntu 24.04+, prefer the repository one-line VPS installer with --with-openai and OpenAI Secure MCP Tunnel. Verify Wisp with doctor, verify the tunnel is ready, then guide me through only the unavoidable ChatGPT/OpenAI account steps. Start read-only; if I want management, enable only the capabilities I need and keep destructive operations disabled unless I explicitly request them. For later server changes, inspect first, back up risky files, make the smallest change, test it, check logs, and never claim success without verification.
```

The longer version in [docs/ai-guided-setup.md](docs/ai-guided-setup.md) includes the full decision path.

For a fresh Debian 12 or Ubuntu 24.04+ VPS using ChatGPT/OpenAI, the server-side install is one line:

```bash
curl -fsSL https://raw.githubusercontent.com/BreezeDelegate/wisp-mcp/main/install-vps.sh | sudo bash -s -- --with-openai
```

It installs Wisp MCP, verifies the Wisp API, and installs the official OpenAI tunnel client. Credentials are entered directly in the terminal and are not passed on the command line. The MCP remains private. See [docs/chatgpt.md](docs/chatgpt.md).

## Quick start

Requirements: Python 3.11 or newer and a Wisp Client API token.

```bash
git clone https://github.com/BreezeDelegate/wisp-mcp.git
cd wisp-mcp
./setup.sh
```

The setup script creates an isolated virtual environment and runs the configuration wizard. It starts in read-only mode.

For an existing Python environment:

```bash
python -m pip install .
wisp-mcp init
wisp-mcp doctor
wisp-mcp
```

`wisp-mcp` uses stdio by default, which fits local MCP clients. `wisp-mcp serve` exposes Streamable HTTP for remote deployments.

## Configuration

The default configuration file is:

```text
~/.config/wisp-mcp/config.env
```

You can use another file with `WISP_CONFIG_FILE`, or provide environment variables directly.

Required values:

```env
WISP_PANEL_URL=https://panel.example.com
WISP_API_TOKEN=your_token
```

`WISP_SERVER_ID` is optional. When set, tools can omit `server_id`.

Changing operations are disabled by default. Enable only what you need:

```env
WISP_ALLOW_COMMANDS=true
WISP_ALLOW_FILE_WRITES=true
WISP_ALLOW_POWER=true
WISP_ALLOW_BACKUPS=true
WISP_ALLOW_DATABASES=false
WISP_ALLOW_SERVER_SETTINGS=false
WISP_ALLOW_DESTRUCTIVE=false
```

Destructive access is a separate switch. Deleting files or backups, restoring backups, rotating database passwords, deleting databases, force-killing a server, and running panel update actions require it.

## Tools

Read-only tools cover servers, resources, audit logs, directories, files, log tails, backups, and databases.

Optional write tools cover file changes, console commands, power control, backups, databases, monitoring/support toggles, and Wisp update actions.

The server publishes operating instructions to MCP clients: inspect first, back up before risky changes, make the smallest change, and verify status and logs afterward.

See [docs/getting-started.md](docs/getting-started.md) for a local setup, [docs/ai-guided-setup.md](docs/ai-guided-setup.md) for assisted onboarding, [docs/vps.md](docs/vps.md) for VPS sizing, and [docs/operations.md](docs/operations.md) for deployment and safety details.

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

The MCP endpoint is `/mcp`. Health is available at `/health`.

## Docker

```bash
cp .env.example .env
# edit .env
docker compose up -d --build
```

The example compose file publishes the service on localhost only.

## VeryCloud

VeryCloud uses Wisp. Set:

```env
WISP_PANEL_URL=https://panel.verycloud.fr
```

Then use a Client API token from your Wisp account. See [docs/verycloud.md](docs/verycloud.md).

## Security

API and MCP tokens are never returned by tools. Remote HTTP fails closed unless authentication is configured. File paths and object IDs are validated, write size is limited, and server-changing capabilities are opt-in.

Report security issues privately as described in [SECURITY.md](SECURITY.md).

## License

MIT
