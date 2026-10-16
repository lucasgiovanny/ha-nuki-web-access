"""Config flow: one Nuki Web API token per account."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import voluptuous as vol
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_API_TOKEN
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import NukiWebApi, NukiWebAuthError, NukiWebError
from .const import DOMAIN

SCHEMA = vol.Schema({vol.Required(CONF_API_TOKEN): str})


class NukiWebAccessConfigFlow(ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def _validate(self, token: str) -> tuple[list[dict[str, Any]], dict[str, str]]:
        try:
            locks = await NukiWebApi(async_get_clientsession(self.hass), token).async_smartlocks()
        except NukiWebAuthError:
            return [], {"base": "invalid_auth"}
        except NukiWebError:
            return [], {"base": "cannot_connect"}
        if not locks:
            return [], {"base": "no_locks"}
        return locks, {}

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            token = user_input[CONF_API_TOKEN].strip().removeprefix("Bearer ").strip()
            locks, errors = await self._validate(token)
            if not errors:
                await self.async_set_unique_id(str(locks[0]["accountId"]))
                self._abort_if_unique_id_configured()
                return self.async_create_entry(title="Nuki Web", data={CONF_API_TOKEN: token})
        return self.async_show_form(step_id="user", data_schema=SCHEMA, errors=errors)

    async def async_step_reauth(self, entry_data: Mapping[str, Any]) -> ConfigFlowResult:
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            token = user_input[CONF_API_TOKEN].strip().removeprefix("Bearer ").strip()
            locks, errors = await self._validate(token)
            if not errors:
                await self.async_set_unique_id(str(locks[0]["accountId"]))
                self._abort_if_unique_id_mismatch(reason="wrong_account")
                return self.async_update_reload_and_abort(
                    self._get_reauth_entry(), data_updates={CONF_API_TOKEN: token}
                )
        return self.async_show_form(step_id="reauth_confirm", data_schema=SCHEMA, errors=errors)
