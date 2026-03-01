"""Number platform for SEVI Cloud — filter replacement interval per device."""

from __future__ import annotations

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.const import UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .coordinator import SeviCloudDataUpdateCoordinator
from .data import SeviCloudConfigEntry
from .entity import SeviCloudDeviceEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: SeviCloudConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Create number entities for each device."""
    coordinator = entry.runtime_data.coordinator
    entities: list[NumberEntity] = []

    if coordinator.data:
        for device_id, device_data in coordinator.data.items():
            device_name = device_data.get("name", device_id)
            entities.append(
                SeviCloudFilterMaxRuntimeNumber(
                    coordinator=coordinator,
                    device_id=device_id,
                    device_name=device_name,
                )
            )

    async_add_entities(entities)


class SeviCloudFilterMaxRuntimeNumber(SeviCloudDeviceEntity, NumberEntity):
    """Number entity to configure the filter replacement interval (90–270 days)."""

    _attr_native_min_value = 90
    _attr_native_max_value = 270
    _attr_native_step = 1
    _attr_native_unit_of_measurement = UnitOfTime.DAYS
    _attr_mode = NumberMode.BOX
    _attr_icon = "mdi:air-filter"

    def __init__(
        self,
        coordinator: SeviCloudDataUpdateCoordinator,
        device_id: str,
        device_name: str,
    ) -> None:
        super().__init__(coordinator, device_id, device_name, "filter_max_runtime")
        self._attr_name = "Filter replacement interval"

    @property
    def native_value(self) -> float | None:
        return self._device_data.get("settings", {}).get("filter", {}).get("maxRunTime")

    async def async_set_native_value(self, value: float) -> None:
        await self.coordinator.config_entry.runtime_data.client.async_set_filter_max_runtime(
            self._device_id, int(value)
        )
        await self.coordinator.async_request_refresh()
