# VeryCloud

VeryCloud game servers use the Wisp panel.

Use this panel URL:

```env
WISP_PANEL_URL=https://panel.verycloud.fr
```

Create a Client API token from the account security controls in the panel. Copy the short server ID from the server URL if you want a default server:

```env
WISP_SERVER_ID=ABCDEFGH
```

Then run:

```bash
wisp-mcp doctor
```

No VeryCloud-specific code path is required. The integration uses the standard Wisp Client API.
