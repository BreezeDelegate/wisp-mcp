# Security policy

Wisp MCP uses the WISP Client API. The API token determines which servers and operations the MCP can access. The MCP does not grant direct access to the hosting provider's machine.

## Reporting a vulnerability

Use **GitHub private vulnerability reporting** for this repository if it is enabled. Do not publish exploit details or credentials in a public issue.

Include the affected version, prerequisites, steps to reproduce with test data, observed impact, and a suggested fix if available. Never attach a real Client API token, bearer token, database credential, customer file, or private log.

For non-sensitive bugs or documentation questions, use ordinary GitHub issues.

## Safe deployment

- Use a Client API token with the least privilege available in your panel.
- Keep API tokens and MCP bearer tokens outside Git, logs, screenshots and AI conversations.
- Start read-only. Enable file changes, power, console, backups or database operations only when required.
- Leave **WISP_ALLOW_DESTRUCTIVE=false** for routine administration.
- Treat **WISP_ALLOW_COMMANDS=true** and file-write permissions as potentially destructive even when the separate destructive flag is off. Game console commands and configuration edits can alter or erase data.
- A remote HTTP deployment should use TLS, a strong **WISP_MCP_AUTH_TOKEN**, an explicit host allowlist and narrow network exposure. Do not opt into unauthenticated remote operation.
- Reading files and logs may expose secrets or customer data. Restrict the token's scope and avoid sending sensitive content to AI clients.
- Back up before risky changes and verify the server after applying them.

## Security boundaries and limitations

The repository validates server IDs and file paths, restricts several categories of write operations behind capability flags, and requires HTTP authentication for ordinary remote deployments by default. These controls reduce risk; they are not a complete sandbox or a substitute for panel-side authorization.

SHA-256 checks on selected file-edit operations detect changes between reads and writes, but they are not a transactional lock or an atomic compare-and-swap supported by WISP.

Security fixes should include a regression test covering both the abusive case and the legitimate workflow.
