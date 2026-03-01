"""Base entity classes for SEVI Cloud integration."""

from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import SeviCloudDataUpdateCoordinator


class SeviCloudDeviceEntity(CoordinatorEntity[SeviCloudDataUpdateCoordinator]):
    """Base class for entities that belong to a specific ventilation device."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: SeviCloudDataUpdateCoordinator,
        device_id: str,
        device_name: str,
        entity_key: str,
    ) -> None:
        super().__init__(coordinator)
        self._device_id = device_id
        self._attr_unique_id = f"{device_id}_{entity_key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, device_id)},
            name=device_name,
            manufacturer="SEVI / SEC Smart",
            model="SEVi Ventilation Unit",
        )

    @property
    def _device_data(self) -> dict:
        """Return coordinator data for this device, or empty dict."""
        if self.coordinator.data is None:
            return {}
        return self.coordinator.data.get(self._device_id, {})


class SeviCloudAreaEntity(SeviCloudDeviceEntity):
    """Base class for entities tied to a specific ventilation area."""

    def __init__(
        self,
        coordinator: SeviCloudDataUpdateCoordinator,
        device_id: str,
        device_name: str,
        area_id: int,
        area_label: str,
        entity_key: str,
    ) -> None:
        super().__init__(
            coordinator,
            device_id,
            device_name,
            f"area{area_id}_{entity_key}",
        )
        self._area_id = area_id
        self._area_label = area_label
