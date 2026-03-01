"""Fan platform for SEVI Cloud — one entity per active ventilation area."""

from __future__ import annotations

from typing import Any

from homeassistant.components.fan import FanEntity, FanEntityFeature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.util.percentage import (
    percentage_to_ordered_list_item,
)

from .const import (
    FAN_PRESET_MODES,
    MANUAL_MODES,
    MODE_FANS_OFF,
    MODE_INACTIVE,
    MODE_MANUAL_1,
    SPEED_TO_PCT,
)
from .coordinator import SeviCloudDataUpdateCoordinator
from .data import SeviCloudConfigEntry, get_active_areas, get_area_mode
from .entity import SeviCloudAreaEntity

# Ordered list used for percentage↔speed mapping (lowest to highest).
_SPEED_LIST = list(MANUAL_MODES)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: SeviCloudConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up fan entities for all active areas across all devices."""
    coordinator = entry.runtime_data.coordinator
    entities: list[SeviCloudFan] = []

    if coordinator.data:
        for device_id, device_data in coordinator.data.items():
            device_name = device_data.get("name", device_id)
            for area_id, area_label in get_active_areas(device_data):
                entities.append(
                    SeviCloudFan(
                        coordinator=coordinator,
                        device_id=device_id,
                        device_name=device_name,
                        area_id=area_id,
                        area_label=area_label,
                    )
                )

    async_add_entities(entities)


class SeviCloudFan(SeviCloudAreaEntity, FanEntity):
    """Fan entity representing one ventilation area."""

    _attr_supported_features = (
        FanEntityFeature.SET_SPEED
        | FanEntityFeature.PRESET_MODE
        | FanEntityFeature.TURN_ON
        | FanEntityFeature.TURN_OFF
    )
    _attr_preset_modes = FAN_PRESET_MODES

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
            entity_key="fan",
        )
        # The entity name is the area label (e.g. "Schlafzimmer").
        self._attr_name = area_label

    # ------------------------------------------------------------------
    # State
    # ------------------------------------------------------------------

    @property
    def _current_mode(self) -> str:
        return get_area_mode(self._device_data, self._area_id)

    @property
    def is_on(self) -> bool:
        mode = self._current_mode
        return mode not in (MODE_FANS_OFF, MODE_INACTIVE, "")

    @property
    def percentage(self) -> int | None:
        mode = self._current_mode
        if mode in SPEED_TO_PCT:
            return SPEED_TO_PCT[mode]
        return None

    @property
    def preset_mode(self) -> str | None:
        mode = self._current_mode
        if mode in FAN_PRESET_MODES:
            return mode
        return None

    @property
    def speed_count(self) -> int:
        return len(_SPEED_LIST)

    # ------------------------------------------------------------------
    # Commands
    # ------------------------------------------------------------------

    async def async_turn_on(
        self,
        percentage: int | None = None,
        preset_mode: str | None = None,
        **kwargs: Any,
    ) -> None:
        """Turn on the fan, optionally at a specific speed or preset."""
        if preset_mode is not None:
            mode = preset_mode
        elif percentage is not None:
            mode = percentage_to_ordered_list_item(_SPEED_LIST, percentage)
        else:
            mode = MODE_MANUAL_1
        await self._set_mode(mode)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off the fan (Fans off)."""
        await self._set_mode(MODE_FANS_OFF)

    async def async_set_percentage(self, percentage: int) -> None:
        """Set fan speed via a percentage (mapped to Manual 1–6)."""
        mode = percentage_to_ordered_list_item(_SPEED_LIST, percentage)
        await self._set_mode(mode)

    async def async_set_preset_mode(self, preset_mode: str) -> None:
        """Set a named ventilation preset."""
        await self._set_mode(preset_mode)

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    async def _set_mode(self, mode: str) -> None:
        await self.coordinator.config_entry.runtime_data.client.async_set_area_mode(
            self._device_id, self._area_id, mode
        )
        await self.coordinator.async_request_refresh()
