"""Base entity: one keypad code of one smart lock."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from homeassistant.core import callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import NukiWebCoordinator


class NukiCodeEntity(CoordinatorEntity[NukiWebCoordinator]):
    """Entities of every code sit on the smart lock's device, named after the code."""

    _attr_has_entity_name = True

    def __init__(
        self, coordinator: NukiWebCoordinator, smartlock_id: int, code_id: str, key: str
    ) -> None:
        super().__init__(coordinator)
        self.smartlock_id = smartlock_id
        self.code_id = code_id
        self._attr_translation_key = key
        self._attr_translation_placeholders = {"code": self.code["name"]}
        self._attr_unique_id = f"{code_id}_{key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, str(smartlock_id))},
            name=f"{coordinator.data[smartlock_id]['lock'].get('name')} keypad codes",
            manufacturer="Nuki",
            model="Nuki Web",
        )

    @property
    def code(self) -> dict[str, Any]:
        return self.coordinator.data[self.smartlock_id]["codes"][self.code_id]

    @property
    def available(self) -> bool:
        lock = self.coordinator.data.get(self.smartlock_id)
        return super().available and lock is not None and self.code_id in lock["codes"]

    async def _async_update(self, **changes: Any) -> None:
        await self.coordinator.async_update_code(self.smartlock_id, self.code_id, changes)


def add_code_entities(
    entry: Any,
    async_add_entities: Callable[[list[NukiCodeEntity]], None],
    factories: tuple[Callable[[NukiWebCoordinator, int, str], NukiCodeEntity], ...],
) -> None:
    """Add entities for every code now and for codes created later in the Nuki app."""
    coordinator: NukiWebCoordinator = entry.runtime_data
    known: set[str] = set()

    @callback
    def _add_new() -> None:
        new = [
            (smartlock_id, code_id)
            for smartlock_id, lock in coordinator.data.items()
            for code_id in lock["codes"]
            if code_id not in known
        ]
        known.update(code_id for _, code_id in new)
        async_add_entities(
            [
                factory(coordinator, smartlock_id, code_id)
                for smartlock_id, code_id in new
                for factory in factories
            ]
        )

    _add_new()
    entry.async_on_unload(coordinator.async_add_listener(_add_new))
