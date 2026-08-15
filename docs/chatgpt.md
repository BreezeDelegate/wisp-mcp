# ChatGPT and OpenAI

For an always-on private deployment, run Wisp MCP on a Linux VPS and connect it with OpenAI Secure MCP Tunnel. The tunnel is outbound-only, so the MCP server does not need a public listener or inbound firewall rule.

OpenAI currently documents full MCP write/modify actions for ChatGPT Business, Enterprise and Edu. Pro can use custom MCP in developer mode for read/fetch, but not full write control. Check current OpenAI availability before choosing a plan.

## Automated server side

Install Wisp MCP and the official OpenAI tunnel client:

```bash
curl -fsSL https://raw.githubusercontent.com/BreezeDelegate/wisp-mcp/main/install-vps.sh | sudo bash -s -- --with-openai
```

The installer verifies the Wisp API before it finishes.

## OpenAI account steps

In OpenAI Platform:

1. Create or select an MCP tunnel.
2. Associate it with the intended organization/workspace as required by your account setup.
3. Create a separate runtime API key for the tunnel client with Tunnels Read + Use.

Then on the VPS:

```bash
sudo wisp-mcp-openai-setup
```

Enter the tunnel ID and runtime API key only in the terminal prompt.

When the helper reports that the tunnel is ready, create a developer-mode app in ChatGPT, choose Tunnel as the connection type, select the tunnel, scan tools, and create the app. Then start a new chat and select the app from the app/tool picker or invoke it with an @ mention when available.

Current OpenAI documentation:

- https://developers.openai.com/api/docs/guides/secure-mcp-tunnels
- https://help.openai.com/en/articles/12584461-developer-mode-apps-and-full-mcp-connectors-in-chatgpt-beta

OpenAI product availability and UI can change. Follow the current official documentation when it differs from this guide.
