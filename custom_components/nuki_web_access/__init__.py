"""Nuki Web Access: keypad codes from Nuki Web as Home Assistant entities."""

from __future__ import annotations

from homeassistant.const import CONF_API_TOKEN, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import NukiWebApi
from .coordinator import NukiWebConfigEntry, NukiWebCoordinator

PLATFORMS = [Platform.DATETIME, Platform.SWITCH]


async def async_setup_entry(hass: HomeAssistant, entry: NukiWebConfigEntry) -> bool:
    api = NukiWebApi(async_get_clientsession(hass), entry.data[CONF_API_TOKEN])
    coordinator = NukiWebCoordinator(hass, entry, api)
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: NukiWebConfigEntry) -> bool:
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
