#!/usr/bin/env bash
set -euo pipefail
IMAGE="${1:?usage: run-container.sh IMAGE}"
NAME=wisp-mcp-site
NETWORK=coolify

docker image inspect "$IMAGE" >/dev/null
docker rm -f "$NAME" >/dev/null 2>&1 || true
docker run -d --name "$NAME" --restart unless-stopped \
  --network "$NETWORK" --network-alias "$NAME" \
  --user 101 --read-only \
  --tmpfs /tmp:size=4m,mode=1777,noexec,nosuid \
  --tmpfs /var/cache/nginx:size=8m,mode=0755 \
  --tmpfs /var/run:size=2m,mode=0755 \
  --security-opt no-new-privileges:true --cap-drop ALL \
  --pids-limit 100 --memory 128m --cpus 0.50 \
  "$IMAGE" >/dev/null
for _ in {1..30}; do
  if docker exec "$NAME" sh -c "wget -qO- http://127.0.0.1:8080/healthz" 2>/dev/null | grep -qx ok; then
    printf "deployed %s\n" "$IMAGE"
    exit 0
  fi
  sleep 1
done
docker logs --tail 100 "$NAME" >&2 || true
exit 1
