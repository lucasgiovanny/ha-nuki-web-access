"""Polls Nuki Web for the keypad codes and applies changes to them."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed, HomeAssistantError
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import NukiWebApi, NukiWebAuthError, NukiWebError
from .codes import build_update, mismatches
from .const import AUTH_TYPE_KEYPAD_CODE, DOMAIN, SCAN_INTERVAL

_LOGGER = logging.getLogger(__name__)

# Nuki Web can answer 204 without storing the change, so each update is read back.
VERIFY_DELAYS = (2, 5, 10)
UPDATE_ATTEMPTS = 2

type NukiWebConfigEntry = ConfigEntry[NukiWebCoordinator]


class NukiWebCoordinator(DataUpdateCoordinator[dict[int, dict[str, Any]]]):
    """Holds each smart lock with its keypad codes, keyed by smart lock id and code id."""

    config_entry: NukiWebConfigEntry

    def __init__(self, hass: HomeAssistant, entry: NukiWebConfigEntry, api: NukiWebApi) -> None:
        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name=DOMAIN,
            update_interval=SCAN_INTERVAL,
        )
        self.api = api
        self._update_lock = asyncio.Lock()

    async def _async_update_data(self) -> dict[int, dict[str, Any]]:
        try:
            locks = await self.api.async_smartlocks()
            data = {}
            for lock in locks:
                auths = await self.api.async_auths(lock["smartlockId"])
                data[lock["smartlockId"]] = {
                    "lock": lock,
                    "codes": {
                        auth["id"]: auth
                        for auth in auths
                        if auth.get("type") == AUTH_TYPE_KEYPAD_CODE
                    },
                }
            return data
        except NukiWebAuthError as err:
            raise ConfigEntryAuthFailed(str(err)) from err
        except NukiWebError as err:
            raise UpdateFailed(str(err)) from err

    async def async_update_code(
        self, smartlock_id: int, code_id: str, changes: dict[str, Any]
    ) -> None:
        """Send the changes and wait until Nuki Web shows them, retrying once."""
        async with self._update_lock:
            auth = self.data[smartlock_id]["codes"][code_id]
            try:
                for _attempt in range(UPDATE_ATTEMPTS):
                    await self.api.async_update_auth(
                        smartlock_id, code_id, build_update(auth, changes)
                    )
                    for delay in VERIFY_DELAYS:
                        await asyncio.sleep(delay)
                        auth = await self.api.async_auth(smartlock_id, code_id)
                        if not mismatches(auth, changes):
                            self.data[smartlock_id]["codes"][code_id] = auth
                            self.async_update_listeners()
                            return
            except NukiWebAuthError as err:
                self.config_entry.async_start_reauth(self.hass)
                raise HomeAssistantError(str(err)) from err
            except NukiWebError as err:
                raise HomeAssistantError(str(err)) from err

            self.data[smartlock_id]["codes"][code_id] = auth
            self.async_update_listeners()
            raise HomeAssistantError(
                f"Nuki Web did not apply {', '.join(mismatches(auth, changes))} to keypad code "
                f"{auth.get('name')}"
            )
