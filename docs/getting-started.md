# Getting started

## 1. Create a Wisp API token

Open your Wisp panel, go to your account security controls, and create a Client API token. Treat it like a password.

Your server ID is the short identifier shown in the server URL. For example, `/server/ABCDEFGH` uses `ABCDEFGH`.

## 2. Install

Linux and macOS:

```bash
git clone https://github.com/BreezeDelegate/wisp-mcp.git
cd wisp-mcp
./setup.sh
```

Windows PowerShell:

```powershell
git clone https://github.com/BreezeDelegate/wisp-mcp.git
cd wisp-mcp
.\setup.ps1
```

The setup asks for the panel URL, API token, and optional default server ID. The token is stored in a user-only configuration file.

## 3. Check the connection

```bash
wisp-mcp doctor
```

A successful check confirms the token can list servers and, when configured, read the default server status.

## 4. Connect an MCP client

For local clients, use the `wisp-mcp` executable with the `stdio` argument or no argument.

Generic configuration shape:

```json
{
  "mcpServers": {
    "wisp": {
      "command": "/path/to/wisp-mcp",
      "args": ["stdio"]
    }
  }
}
```

The setup script prints the exact executable path it installed.

## 5. Enable write access only when needed

Start read-only. To edit server files and use the console:

```env
WISP_ALLOW_FILE_WRITES=true
WISP_ALLOW_COMMANDS=true
```

Add backup and power access when useful:

```env
WISP_ALLOW_BACKUPS=true
WISP_ALLOW_POWER=true
```

Keep `WISP_ALLOW_DESTRUCTIVE=false` unless you explicitly need destructive operations.
