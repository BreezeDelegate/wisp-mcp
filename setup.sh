#!/usr/bin/env bash
set -euo pipefail

command -v python3 >/dev/null 2>&1 || { echo "Python 3 is required." >&2; exit 1; }
python3 - <<'PY'
import sys
if sys.version_info < (3, 11):
    raise SystemExit("Python 3.11 or newer is required.")
PY

base="${XDG_DATA_HOME:-$HOME/.local/share}/wisp-mcp"
venv="$base/venv"
mkdir -p "$base"
python3 -m venv "$venv"
"$venv/bin/python" -m pip install --upgrade pip
"$venv/bin/python" -m pip install .
"$venv/bin/wisp-mcp" init
"$venv/bin/wisp-mcp" doctor
printf '\nInstalled executable:\n%s\n' "$venv/bin/wisp-mcp"
printf '\nUse this command in a local MCP client:\n%s stdio\n' "$venv/bin/wisp-mcp"
