# AI-guided setup

This path is for someone who wants an assistant to guide the entire setup.

Copy the prompt below into your assistant. It tells the assistant to confirm WISP first, use this repository as the source of truth, keep credentials out of chat, choose the correct MCP client path, verify every step, and minimize manual work.

```text
Help me install Wisp MCP and connect it to my AI client.

Use https://github.com/BreezeDelegate/wisp-mcp as the source of truth. Read its current README and setup docs before giving commands. Reply in my language and guide me one step at a time.

First help me confirm that my game host actually uses the WISP panel. Use the repository panel-recognition guide and explain that WISP can be white-labelled, so colors and logos may differ. If I am still unsure, tell me to ask my host whether I have a WISP Client API token.

Then determine what I already have: a WISP-compatible panel, a Client API token, a Linux machine or VPS, and which MCP-capable AI client I want to use. Never ask me to paste API tokens, private keys, passwords, or tunnel runtime keys into chat. When a secret is required, tell me exactly where to enter it directly in the terminal, setup wizard, or provider UI.

If I need an always-on machine, help me choose the smallest sensible Linux VPS for my actual workload. Wisp MCP itself is lightweight; do not oversell hardware. Explain that the VPS running Wisp MCP does not have to host the game server. If I also want websites, databases, builds, or other services on the same VPS, size it for those workloads separately.

On Debian 12 or Ubuntu 24.04+, prefer the repository one-line VPS installer. Use --with-openai only when I chose ChatGPT and an OpenAI Secure MCP Tunnel is appropriate. Verify the WISP API with doctor before moving on.

Choose the client path from docs/clients.md. For ChatGPT, use the current official OpenAI Secure MCP Tunnel documentation rather than remembered UI labels. For Claude Code, prefer standard stdio and use SSH as the stdio command when Wisp MCP is on a remote VPS. For another client, use stdio, Streamable HTTP, or the MCP Bundle only if that client supports it.

After connection, start read-only. Ask whether I want standard server management. If I do, enable only the capabilities needed for file editing, console commands, power control, backups, databases, or server settings. Keep destructive operations disabled unless I explicitly request a destructive task.

Before any server change through Wisp MCP, inspect the relevant files, server state, and logs. Back up or copy files before risky edits when possible. Make the smallest useful change, test it, inspect logs afterward, and report the result. Do not claim success without verification.
```

## One-line VPS install

Generic MCP client:

```bash
curl -fsSL https://raw.githubusercontent.com/BreezeDelegate/wisp-mcp/main/install-vps.sh | sudo bash
```

ChatGPT with OpenAI Secure MCP Tunnel:

```bash
curl -fsSL https://raw.githubusercontent.com/BreezeDelegate/wisp-mcp/main/install-vps.sh | sudo bash -s -- --with-openai
```

The installer asks for the WISP panel URL, optional default server ID, and WISP Client API token directly in the terminal. It starts read-only.

See [clients.md](clients.md) for the next step after installation.
