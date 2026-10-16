"""Enabled switch per keypad code, which also carries the set_access action."""

from __future__ import annotations

from datetime import datetime, time
from typing import Any

import voluptuous as vol
from homeassistant.components.switch import SwitchEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers import entity_platform
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.util import dt as dt_util

from .codes import (
    WEEKDAYS,
    mask_from_weekdays,
    minutes_to_time,
    parse_date,
    time_to_minutes,
    weekdays_from_mask,
)
from .coordinator import NukiWebConfigEntry
from .entity import NukiCodeEntity, add_code_entities

SERVICE_SET_ACCESS = "set_access"


async def async_setup_entry(
    hass: HomeAssistant,
    entry: NukiWebConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    add_code_entities(entry, async_add_entities, (NukiCodeEnabledSwitch,))
    entity_platform.async_get_current_platform().async_register_entity_service(
        SERVICE_SET_ACCESS,
        {
            vol.Optional("enabled"): cv.boolean,
            vol.Optional("valid_from"): cv.datetime,
            vol.Optional("valid_until"): cv.datetime,
            vol.Optional("no_date_limit"): cv.boolean,
            vol.Optional("weekdays"): vol.All(cv.ensure_list, [vol.In(WEEKDAYS)]),
            vol.Optional("from_time"): cv.time,
            vol.Optional("until_time"): cv.time,
        },
        "async_set_access",
    )


class NukiCodeEnabledSwitch(NukiCodeEntity, SwitchEntity):
    """Whether the keypad code (and its fingerprints) opens the door at all."""

    def __init__(self, coordinator, smartlock_id: int, code_id: str) -> None:
        super().__init__(coordinator, smartlock_id, code_id, "enabled")

    @property
    def is_on(self) -> bool:
        return bool(self.code.get("enabled"))

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        code = self.code
        return {
            # The id the lock reports in MQTT lock action events for this code.
            "auth_id": code.get("authId"),
            "weekdays": weekdays_from_mask(code.get("allowedWeekDays")),
            "from_time": minutes_to_time(code.get("allowedFromTime")),
            "until_time": minutes_to_time(code.get("allowedUntilTime")),
            "valid_from": parse_date(code.get("allowedFromDate")),
            "valid_until": parse_date(code.get("allowedUntilDate")),
            "last_used": parse_date(code.get("lastActiveDate")),
            "fingerprints": len(code.get("fingerprints") or {}),
            "pending_sync": code.get("operationId") is not None,
            "sync_error": code.get("error"),
        }

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self._async_update(enabled=True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self._async_update(enabled=False)

    async def async_set_access(
        self,
        enabled: bool | None = None,
        valid_from: datetime | None = None,
        valid_until: datetime | None = None,
        no_date_limit: bool = False,
        weekdays: list[str] | None = None,
        from_time: time | None = None,
        until_time: time | None = None,
    ) -> None:
        changes: dict[str, Any] = {}
        if enabled is not None:
            changes["enabled"] = enabled
        if no_date_limit:
            changes["allowedFromDate"] = None
            changes["allowedUntilDate"] = None
        if valid_from is not None:
            changes["allowedFromDate"] = dt_util.as_utc(valid_from)
        if valid_until is not None:
            changes["allowedUntilDate"] = dt_util.as_utc(valid_until)
        if weekdays is not None:
            changes["allowedWeekDays"] = mask_from_weekdays(weekdays)
        if from_time is not None:
            changes["allowedFromTime"] = time_to_minutes(from_time)
        if until_time is not None:
            changes["allowedUntilTime"] = time_to_minutes(until_time)
        if changes:
            await self._async_update(**changes)
