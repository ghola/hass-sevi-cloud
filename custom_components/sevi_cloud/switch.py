"""Switch platform for SEVI Cloud.

Switches:
  - Boost (per active area) — sets/clears "Boost ventilation" mode
  - Summer mode (per device) — toggles summer ventilation
  - Time auto-sync (per device) — toggles automatic clock synchronisation
"""

from __future__ import annotations

from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import MODE_BOOST, MODE_MANUAL_1
from .coordinator import SeviCloudDataUpdateCoordinator
from .data import SeviCloudConfigEntry, get_active_areas, get_area_mode
from .entity import SeviCloudAreaEntity, SeviCloudDeviceEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: SeviCloudConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Create switch entities for all devices and their active areas."""
    coordinator = entry.runtime_data.coordinator
    entities: list[SwitchEntity] = []

    if coordinator.data:
        for device_id, device_data in coordinator.data.items():
            device_name = device_data.get("name", device_id)

            # Per-area boost switches.
            for area_id, area_label in get_active_areas(device_data):
                entities.append(
                    SeviCloudBoostSwitch(
                        coordinator=coordinator,
                        device_id=device_id,
                        device_name=device_name,
                        area_id=area_id,
                        area_label=area_label,
                    )
                )

            # Per-device settings switches.
            entities.append(
                SeviCloudSummerModeSwitch(
                    coordinator=coordinator,
                    device_id=device_id,
                    device_name=device_name,
                )
            )
            entities.append(
                SeviCloudTimeAutosyncSwitch(
                    coordinator=coordinator,
                    device_id=device_id,
                    device_name=device_name,
                )
            )

    async_add_entities(entities)


# ---------------------------------------------------------------------------
# Per-area boost switch
# ---------------------------------------------------------------------------


class SeviCloudBoostSwitch(SeviCloudAreaEntity, SwitchEntity):
    """Switch that activates/deactivates boost ventilation for one area."""

    def __init__(
        self,
        coordinator: SeviCloudDataUpdateCoordinator,
        device_id: str,
        device_name: str,
        area_id: int,
        area_label: str,
    ) -> None:
        super().__init__(
            coordinator,
            device_id,
            device_name,
            area_id,
            area_label,
            entity_key="boost",
        )
        self._attr_name = f"{area_label} Boost"
        self._attr_icon = "mdi:fan-chevron-up"

    @property
    def is_on(self) -> bool:
        return get_area_mode(self._device_data, self._area_id) == MODE_BOOST

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self.coordinator.config_entry.runtime_data.client.async_set_area_mode(
            self._device_id, self._area_id, MODE_BOOST
        )
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        # Deactivate boost: return to minimum manual speed.
        await self.coordinator.config_entry.runtime_data.client.async_set_area_mode(
            self._device_id, self._area_id, MODE_MANUAL_1
        )
        await self.coordinator.async_request_refresh()


# ---------------------------------------------------------------------------
# Per-device settings switches
# ---------------------------------------------------------------------------


class SeviCloudSummerModeSwitch(SeviCloudDeviceEntity, SwitchEntity):
    """Switch that enables/disables summer ventilation mode (no heat recovery)."""

    def __init__(
        self,
        coordinator: SeviCloudDataUpdateCoordinator,
        device_id: str,
        device_name: str,
    ) -> None:
        super().__init__(coordinator, device_id, device_name, "summer_mode")
        self._attr_name = "Summer mode"
        self._attr_icon = "mdi:weather-sunny"

    @property
    def is_on(self) -> bool:
        return self._device_data.get("settings", {}).get("summermode", False)

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self.coordinator.config_entry.runtime_data.client.async_set_summer_mode(
            self._device_id, enabled=True
        )
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self.coordinator.config_entry.runtime_data.client.async_set_summer_mode(
            self._device_id, enabled=False
        )
        await self.coordinator.async_request_refresh()


class SeviCloudTimeAutosyncSwitch(SeviCloudDeviceEntity, SwitchEntity):
    """Switch that enables/disables automatic clock synchronisation."""

    def __init__(
        self,
        coordinator: SeviCloudDataUpdateCoordinator,
        device_id: str,
        device_name: str,
    ) -> None:
        super().__init__(coordinator, device_id, device_name, "time_autosync")
        self._attr_name = "Time auto-sync"
        self._attr_icon = "mdi:clock-sync"

    @property
    def is_on(self) -> bool:
        return self._device_data.get("settings", {}).get("deviceTime", {}).get("autoSynch", True)

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self.coordinator.config_entry.runtime_data.client.async_set_device_time_autosync(
            self._device_id, enabled=True
        )
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self.coordinator.config_entry.runtime_data.client.async_set_device_time_autosync(
            self._device_id, enabled=False
        )
        await self.coordinator.async_request_refresh()
