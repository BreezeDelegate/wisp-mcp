# AI-guided setup

This path is for someone who wants an assistant to guide the entire setup.

Copy the prompt below into your assistant. It tells the assistant to use this repository as the source of truth, keep credentials out of chat, verify every step, and minimize manual work.

```text
Help me install Wisp MCP and connect it to my AI client.

Use https://github.com/BreezeDelegate/wisp-mcp as the source of truth. Read its current README and setup docs before giving commands. Reply in my language and guide me one step at a time.

First determine what I already have: a Wisp-compatible panel, a Client API token, a Linux machine or VPS, and which AI client I want to use. Never ask me to paste API tokens, private keys, passwords, or tunnel runtime keys into chat. When a secret is required, tell me exactly where to enter it directly in the terminal or provider UI.

If I need an always-on machine, help me choose the smallest sensible Linux VPS for my actual workload. Wisp MCP itself is lightweight; do not oversell hardware. Explain that the VPS running Wisp MCP does not have to host the game server. If I also want websites, databases, builds, or other services on the same VPS, size it for those workloads separately.

For a Debian 12 or Ubuntu 24.04+ VPS and ChatGPT/OpenAI, prefer the repository one-line VPS installer with --with-openai. Verify the Wisp API with doctor before moving on. Keep the MCP private and prefer OpenAI Secure MCP Tunnel instead of opening a public MCP port.

For OpenAI, use the current official Secure MCP Tunnel documentation rather than remembered UI labels. Guide me through the unavoidable account steps: create or select a tunnel, create a separate runtime API key with the required tunnel permissions, associate the tunnel with the intended ChatGPT workspace when needed, then run sudo wisp-mcp-openai-setup on the VPS and enter the tunnel ID and runtime key there, not in chat. Verify the tunnel is ready before asking me to create or scan the ChatGPT app.

After connection, start read-only. Ask whether I want standard server management. If I do, enable only the capabilities needed for file editing, console commands, power control, and backups. Keep destructive operations disabled unless I explicitly request them.

Before any server change through Wisp MCP, inspect the relevant files, server state, and logs. Back up or copy files before risky edits when possible. Make the smallest useful change, test it, inspect logs afterward, and report the result. Do not claim success without verification.
```

## One-line VPS install

For ChatGPT/OpenAI on a fresh Debian 12 or Ubuntu 24.04+ VPS:

```bash
curl -fsSL https://raw.githubusercontent.com/BreezeDelegate/wisp-mcp/main/install-vps.sh | sudo bash -s -- --with-openai
```

The installer asks for the Wisp panel URL, optional default server ID, and Wisp Client API token directly in the terminal. It starts read-only and does not expose an inbound MCP port.

After the OpenAI tunnel and runtime key exist, run:

```bash
sudo wisp-mcp-openai-setup
```

The helper validates the tunnel and installs it as a hardened systemd service.
