# Connect an AI client

Wisp MCP is not tied to one AI product. It implements standard Model Context Protocol transports, so any MCP client that supports **stdio** or **Streamable HTTP** can use it.

The AI client is a separate layer from the WISP panel connection:

1. Wisp MCP connects to your WISP panel with a Client API token.
2. Your AI client connects to Wisp MCP.
3. Capability switches decide what the AI is allowed to change.

## ChatGPT

For an always-on VPS, keep Wisp MCP private and use OpenAI Secure MCP Tunnel.

Install with the tunnel helper:

```bash
curl -fsSL https://raw.githubusercontent.com/BreezeDelegate/wisp-mcp/main/install-vps.sh | sudo bash -s -- --with-openai
```

After creating the tunnel and its runtime key in your OpenAI account:

```bash
sudo wisp-mcp-openai-setup
```

Then add the resulting MCP app in ChatGPT Developer Mode and scan its tools. OpenAI changes availability and UI over time, so use the current official documentation when it differs from this guide:

- https://developers.openai.com/api/docs/guides/secure-mcp-tunnels
- https://help.openai.com/en/articles/12584461-developer-mode-apps-and-full-mcp-connectors-in-chatgpt-beta

## Claude Code

Claude Code supports MCP servers directly from its CLI.

If Claude Code runs on the same machine as Wisp MCP:

```bash
claude mcp add --scope user wisp -- /usr/local/bin/wisp-mcp-stdio
```

If Wisp MCP runs on a remote VPS, SSH can carry the stdio transport without exposing an MCP HTTP port:

```bash
claude mcp add --scope user wisp -- ssh user@your-vps /usr/local/bin/wisp-mcp-stdio
```

Use SSH keys so the connection can start without an interactive password prompt, then verify:

```bash
claude mcp get wisp
```

Current Anthropic MCP documentation:

- https://docs.anthropic.com/en/docs/mcp
- https://docs.anthropic.com/en/docs/claude-code/mcp

## Claude Desktop and other desktop clients

Use the `.mcpb` artifact from the latest GitHub release if your client supports MCP Bundles. Otherwise configure the standard stdio command:

```text
/usr/local/bin/wisp-mcp-stdio
```

For a local Python installation, use the installed `wisp-mcp` executable instead.

## Other MCP clients and agents

Wisp MCP supports the two standard MCP deployment shapes:

- **stdio** for a client that can launch a local command, including an SSH command to a remote VPS;
- **Streamable HTTP** for a remote MCP endpoint behind authentication, a reverse proxy, VPN, or private tunnel.

Run the HTTP transport with:

```bash
wisp-mcp serve
```

Do not expose an unauthenticated MCP endpoint directly to the Internet. See [operations.md](operations.md) for the security settings.

## Compatibility rule

A product does not need a special "Wisp MCP integration". It needs MCP client support and one of the transports above. Products without MCP support cannot use Wisp MCP directly.
