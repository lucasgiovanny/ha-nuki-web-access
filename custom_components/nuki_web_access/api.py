"""Small client for the Nuki Web API."""

from __future__ import annotations

import json
from typing import Any

import aiohttp

from .const import API_URL


class NukiWebError(Exception):
    """Nuki Web could not be reached or answered with an error."""


class NukiWebAuthError(NukiWebError):
    """The API token is missing, revoked or lacks a permission."""


class NukiWebApi:
    """Reads smart locks and their authorizations, and updates authorizations."""

    def __init__(self, session: aiohttp.ClientSession, token: str) -> None:
        self._session = session
        self._headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}

    async def _request(self, method: str, path: str, body: dict[str, Any] | None = None) -> Any:
        try:
            async with self._session.request(
                method,
                f"{API_URL}/{path}",
                headers=self._headers,
                json=body,
                timeout=aiohttp.ClientTimeout(total=20),
            ) as response:
                if response.status in (401, 403):
                    raise NukiWebAuthError(f"Nuki Web refused the token (HTTP {response.status})")
                if response.status >= 400:
                    raise NukiWebError(f"Nuki Web answered HTTP {response.status} for {path}")
                text = await response.text()
                return json.loads(text) if text else None
        except (aiohttp.ClientError, TimeoutError) as err:
            raise NukiWebError(f"Nuki Web could not be reached: {err}") from err

    async def async_smartlocks(self) -> list[dict[str, Any]]:
        return await self._request("GET", "smartlock") or []

    async def async_auths(self, smartlock_id: int) -> list[dict[str, Any]]:
        return await self._request("GET", f"smartlock/{smartlock_id}/auth") or []

    async def async_auth(self, smartlock_id: int, auth_id: str) -> dict[str, Any]:
        return await self._request("GET", f"smartlock/{smartlock_id}/auth/{auth_id}")

    async def async_update_auth(
        self, smartlock_id: int, auth_id: str, body: dict[str, Any]
    ) -> None:
        await self._request("POST", f"smartlock/{smartlock_id}/auth/{auth_id}", body)
