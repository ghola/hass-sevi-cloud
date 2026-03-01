"""Button platform for SEVI Cloud — filter reset per device."""

from __future__ import annotations

from homeassistant.components.button import ButtonEntity
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
    """Create a filter-reset button for each device."""
    coordinator = entry.runtime_data.coordinator
    entities: list[ButtonEntity] = []

    if coordinator.data:
        for device_id, device_data in coordinator.data.items():
            device_name = device_data.get("name", device_id)
            entities.append(
                SeviCloudFilterResetButton(
                    coordinator=coordinator,
                    device_id=device_id,
                    device_name=device_name,
                )
            )

    async_add_entities(entities)


class SeviCloudFilterResetButton(SeviCloudDeviceEntity, ButtonEntity):
    """Button that marks the air filter as replaced."""

    def __init__(
        self,
        coordinator: SeviCloudDataUpdateCoordinator,
        device_id: str,
        device_name: str,
    ) -> None:
        super().__init__(coordinator, device_id, device_name, "filter_reset")
        self._attr_name = "Reset filter"
        self._attr_icon = "mdi:air-filter"

    async def async_press(self) -> None:
        """Reset the filter runtime counter."""
        await self.coordinator.config_entry.runtime_data.client.async_reset_filter(self._device_id)
        await self.coordinator.async_request_refresh()
