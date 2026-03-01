"""Sensor platform for SEVI Cloud — filter remaining days per device."""

from __future__ import annotations

from homeassistant.components.sensor import SensorEntity, SensorStateClass
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
    """Create sensor entities for each device."""
    coordinator = entry.runtime_data.coordinator
    entities: list[SensorEntity] = []

    if coordinator.data:
        for device_id, device_data in coordinator.data.items():
            device_name = device_data.get("name", device_id)
            entities.append(
                SeviCloudFilterRemainingSensor(
                    coordinator=coordinator,
                    device_id=device_id,
                    device_name=device_name,
                )
            )

    async_add_entities(entities)


class SeviCloudFilterRemainingSensor(SeviCloudDeviceEntity, SensorEntity):
    """Sensor showing remaining filter life in days."""

    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = UnitOfTime.DAYS
    _attr_icon = "mdi:air-filter"

    def __init__(
        self,
        coordinator: SeviCloudDataUpdateCoordinator,
        device_id: str,
        device_name: str,
    ) -> None:
        super().__init__(coordinator, device_id, device_name, "filter_remaining")
        self._attr_name = "Filter remaining"

    @property
    def native_value(self) -> int | None:
        return self._device_data.get("telemetry", {}).get("restFilterTime")
