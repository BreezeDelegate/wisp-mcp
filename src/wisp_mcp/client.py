from __future__ import annotations

import asyncio
from typing import Any

import httpx

from .config import Settings, WispError

APP_VERSION = "1.0.0"
MAX_ERROR_TEXT = 500
_REDACT_KEYS = ("token", "secret", "password", "authorization", "cookie", "session")
_RETRYABLE = {429, 502, 503, 504}


def _redact(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            str(key): (
                "[redacted]" if any(marker in str(key).lower() for marker in _REDACT_KEYS) else _redact(item)
            )
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [_redact(item) for item in value[:50]]
    if isinstance(value, str) and len(value) > MAX_ERROR_TEXT:
        return value[:MAX_ERROR_TEXT] + "…"
    return value


def _safe_error(payload: Any, *secrets: str) -> str:
    text = repr(_redact(payload))
    for secret in secrets:
        if secret:
            text = text.replace(secret, "[redacted]")
    return text[:2_000]


class WispClient:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def _headers(self) -> dict[str, str]:
        if not self.settings.api_token:
            raise WispError("WISP_API_TOKEN is not configured")
        return {
            "Authorization": f"Bearer {self.settings.api_token}",
            "Content-Type": "application/json",
            "Accept": "application/vnd.wisp.v1+json",
            "User-Agent": f"wisp-mcp/{APP_VERSION}",
        }

    async def request(
        self,
        method: str,
        path: str,
        *,
        json: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
    ) -> Any:
        url = f"{self.settings.panel_url}{path}"
        timeout = httpx.Timeout(self.settings.timeout)
        try:
            async with httpx.AsyncClient(timeout=timeout, follow_redirects=False) as client:
                response: httpx.Response | None = None
                for attempt in range(2):
                    response = await client.request(
                        method,
                        url,
                        headers=self._headers(),
                        json=json,
                        params=params,
                    )
                    if response.status_code not in _RETRYABLE or attempt == 1:
                        break
                    retry_after = response.headers.get("Retry-After", "")
                    try:
                        delay = min(max(float(retry_after), 0.1), 2.0)
                    except ValueError:
                        delay = 0.25
                    await asyncio.sleep(delay)
        except httpx.TimeoutException as exc:
            raise WispError("Wisp API request timed out") from exc
        except httpx.RequestError as exc:
            raise WispError("Could not reach the Wisp API") from exc

        assert response is not None
        if response.status_code == 204:
            return {"ok": True, "status_code": 204}
        if 300 <= response.status_code < 400:
            return {
                "status_code": response.status_code,
                "location": response.headers.get("Location"),
            }

        try:
            payload: Any = response.json()
        except ValueError:
            payload = {"text": response.text[:MAX_ERROR_TEXT]}

        if response.is_error:
            safe_payload = _safe_error(payload, self.settings.api_token, self.settings.mcp_auth_token)
            raise WispError(f"Wisp API returned HTTP {response.status_code}: {safe_payload}")
        return payload
