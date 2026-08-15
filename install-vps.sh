#!/usr/bin/env bash
set -euo pipefail

repo="BreezeDelegate/wisp-mcp"
with_openai=0

usage() {
  cat <<USAGE
Usage: install-vps.sh [--with-openai]

Installs the latest Wisp MCP release on a Linux VPS, creates a dedicated
service account, stores Wisp credentials outside the repository, and runs
a live API check.

--with-openai  also install the official OpenAI tunnel-client and helper
USAGE
}

for arg in "$@"; do
  case "$arg" in
    --with-openai) with_openai=1 ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown option: $arg" >&2; usage >&2; exit 2 ;;
  esac
done

if [ "$(id -u)" -ne 0 ]; then
  echo "Run this installer as root, normally through sudo." >&2
  exit 1
fi

if [ ! -r /dev/tty ]; then
  echo "An interactive terminal is required for credential entry." >&2
  exit 1
fi

need_packages=()
for cmd in curl python3; do
  command -v "$cmd" >/dev/null 2>&1 || need_packages+=("$cmd")
done
command -v unzip >/dev/null 2>&1 || need_packages+=(unzip)

if [ ${#need_packages[@]} -gt 0 ]; then
  if command -v apt-get >/dev/null 2>&1; then
    apt-get update -qq
    DEBIAN_FRONTEND=noninteractive apt-get install -y -qq python3 python3-venv curl ca-certificates unzip
  else
    echo "Missing required tools: ${need_packages[*]}" >&2
    exit 1
  fi
fi

python3 - <<"PY"
import sys
if sys.version_info < (3, 11):
    raise SystemExit("Python 3.11 or newer is required. Use Debian 12, Ubuntu 24.04+, or another current distribution.")
PY

if ! python3 -m venv --help >/dev/null 2>&1; then
  if command -v apt-get >/dev/null 2>&1; then
    apt-get update -qq
    DEBIAN_FRONTEND=noninteractive apt-get install -y -qq python3-venv
  else
    echo "Python venv support is required." >&2
    exit 1
  fi
fi

release_json=$(curl -fsSL -H "Accept: application/vnd.github+json" "https://api.github.com/repos/$repo/releases/latest")
tag=$(python3 -c "import json,sys; print(json.load(sys.stdin)[\"tag_name\"])" <<<"$release_json")
[ -n "$tag" ] || { echo "Could not resolve the latest release." >&2; exit 1; }

tmp=$(mktemp -d)
trap "rm -rf \"$tmp\"" EXIT
curl -fsSL "https://github.com/$repo/archive/refs/tags/$tag.tar.gz" -o "$tmp/source.tar.gz"
tar -xzf "$tmp/source.tar.gz" -C "$tmp"
source_dir=$(find "$tmp" -mindepth 1 -maxdepth 1 -type d -name "wisp-mcp-*" | head -n 1)
[ -n "$source_dir" ] || { echo "Release archive is invalid." >&2; exit 1; }

if ! id wisp-mcp >/dev/null 2>&1; then
  useradd --system --home-dir /var/lib/wisp-mcp --create-home --shell /usr/sbin/nologin wisp-mcp
fi

install -d -m 0755 /opt/wisp-mcp
rm -rf /opt/wisp-mcp/venv
python3 -m venv /opt/wisp-mcp/venv
/opt/wisp-mcp/venv/bin/python -m pip install -q --upgrade pip
/opt/wisp-mcp/venv/bin/python -m pip install -q "$source_dir"

install -d -m 0750 -o root -g wisp-mcp /etc/wisp-mcp
read -r -p "Wisp panel URL (for example https://panel.verycloud.fr): " panel </dev/tty
read -r -p "Default server ID (optional): " server_id </dev/tty
read -r -s -p "Wisp Client API token: " api_token </dev/tty
printf "\n" >/dev/tty

if [ -z "$panel" ] || [ -z "$api_token" ]; then
  echo "Panel URL and API token are required." >&2
  exit 1
fi

quote_env() {
  python3 -c "import json,sys; print(json.dumps(sys.stdin.read().rstrip(chr(10))))"
}

panel_q=$(printf "%s" "$panel" | quote_env)
token_q=$(printf "%s" "$api_token" | quote_env)
server_q=$(printf "%s" "$server_id" | quote_env)
cat > /etc/wisp-mcp/config.env <<CFG
WISP_PANEL_URL=$panel_q
WISP_API_TOKEN=$token_q
WISP_SERVER_ID=$server_q
WISP_ALLOW_COMMANDS=false
WISP_ALLOW_FILE_WRITES=false
WISP_ALLOW_POWER=false
WISP_ALLOW_BACKUPS=false
WISP_ALLOW_DATABASES=false
WISP_ALLOW_SERVER_SETTINGS=false
WISP_ALLOW_DESTRUCTIVE=false
CFG
chown root:wisp-mcp /etc/wisp-mcp/config.env
chmod 0640 /etc/wisp-mcp/config.env

cat > /usr/local/bin/wisp-mcp-stdio <<"WRAP"
#!/usr/bin/env bash
set -euo pipefail
export WISP_CONFIG_FILE=/etc/wisp-mcp/config.env
exec /opt/wisp-mcp/venv/bin/wisp-mcp stdio
WRAP
chmod 0755 /usr/local/bin/wisp-mcp-stdio

runuser -u wisp-mcp -- env HOME=/var/lib/wisp-mcp WISP_CONFIG_FILE=/etc/wisp-mcp/config.env /opt/wisp-mcp/venv/bin/wisp-mcp doctor

if [ "$with_openai" -eq 1 ]; then
  arch=$(uname -m)
  case "$arch" in
    x86_64|amd64) asset_arch=amd64 ;;
    aarch64|arm64) asset_arch=arm64 ;;
    *) echo "Unsupported architecture for tunnel-client: $arch" >&2; exit 1 ;;
  esac
  tunnel_release=$(curl -fsSL -H "Accept: application/vnd.github+json" "https://api.github.com/repos/openai/tunnel-client/releases/latest")
  tunnel_tag=$(python3 -c "import json,sys; print(json.load(sys.stdin)[\"tag_name\"])" <<<"$tunnel_release")
  asset="tunnel-client-${tunnel_tag}-linux-${asset_arch}.zip"
  base="https://github.com/openai/tunnel-client/releases/download/${tunnel_tag}"
  curl -fsSL "$base/$asset" -o "$tmp/tunnel.zip"
  curl -fsSL "$base/SHA256SUMS.txt" -o "$tmp/SHA256SUMS.txt"
  expected=$(awk -v f="$asset" "\$2 == f {print \$1}" "$tmp/SHA256SUMS.txt")
  actual=$(sha256sum "$tmp/tunnel.zip" | awk "{print \$1}")
  [ -n "$expected" ] && [ "$expected" = "$actual" ] || { echo "tunnel-client checksum verification failed." >&2; exit 1; }
  unzip -q "$tmp/tunnel.zip" -d "$tmp/tunnel"
  install -m 0755 "$tmp/tunnel/tunnel-client" /usr/local/bin/tunnel-client
  curl -fsSL "https://raw.githubusercontent.com/$repo/main/scripts/wisp-mcp-openai-setup" -o "$tmp/wisp-mcp-openai-setup"
  curl -fsSL "https://raw.githubusercontent.com/$repo/main/systemd/wisp-mcp-openai-tunnel.service" -o "$tmp/wisp-mcp-openai-tunnel.service"
  bash -n "$tmp/wisp-mcp-openai-setup"
  install -m 0755 "$tmp/wisp-mcp-openai-setup" /usr/local/sbin/wisp-mcp-openai-setup
  install -m 0644 "$tmp/wisp-mcp-openai-tunnel.service" /etc/systemd/system/wisp-mcp-openai-tunnel.service
  systemctl daemon-reload
fi

printf "\nWisp MCP %s is installed and the Wisp API check passed.\n" "$tag"
printf "Configuration: /etc/wisp-mcp/config.env\n"
printf "Local MCP command: /usr/local/bin/wisp-mcp-stdio\n"
if [ "$with_openai" -eq 1 ]; then
  printf "OpenAI tunnel-client is installed. After creating a tunnel and runtime key, run:\n"
  printf "  sudo wisp-mcp-openai-setup\n"
fi
