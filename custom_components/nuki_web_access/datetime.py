"""Valid-from and valid-until dates per keypad code."""

from __future__ import annotations

from datetime import datetime

from homeassistant.components.datetime import DateTimeEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.util import dt as dt_util

from .codes import parse_date
from .coordinator import NukiWebConfigEntry
from .entity import NukiCodeEntity, add_code_entities


async def async_setup_entry(
    hass: HomeAssistant,
    entry: NukiWebConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    add_code_entities(
        entry,
        async_add_entities,
        (
            lambda c, s, i: NukiCodeDateTime(c, s, i, "valid_from", "allowedFromDate"),
            lambda c, s, i: NukiCodeDateTime(c, s, i, "valid_until", "allowedUntilDate"),
        ),
    )


class NukiCodeDateTime(NukiCodeEntity, DateTimeEntity):
    """One end of the code's date window; unknown means no limit on that side."""

    def __init__(self, coordinator, smartlock_id: int, code_id: str, key: str, field: str) -> None:
        super().__init__(coordinator, smartlock_id, code_id, key)
        self._field = field

    @property
    def native_value(self) -> datetime | None:
        return parse_date(self.code.get(self._field))

    async def async_set_value(self, value: datetime) -> None:
        await self._async_update(**{self._field: dt_util.as_utc(value)})
