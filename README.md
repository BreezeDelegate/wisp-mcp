# Wisp MCP

Wisp MCP exposes the Wisp game panel Client API through Model Context Protocol.

It is designed for day-to-day server administration: inspect status and logs, edit files, send console commands, control power, manage backups, and handle common database or panel operations without giving the MCP process unrestricted host access.

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

See [docs/getting-started.md](docs/getting-started.md) for a beginner setup and [docs/operations.md](docs/operations.md) for deployment and safety details.

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
