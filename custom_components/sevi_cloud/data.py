"""Type definitions and dataclasses for the SEVI Cloud integration."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.loader import Integration

    from .api import SeviCloudApiClient
    from .coordinator import SeviCloudDataUpdateCoordinator

type SeviCloudConfigEntry = ConfigEntry["SeviCloudData"]


@dataclass
class SeviCloudData:
    """Runtime data stored on the config entry."""

    client: SeviCloudApiClient
    coordinator: SeviCloudDataUpdateCoordinator
    integration: Integration


def get_active_areas(device_data: dict[str, Any]) -> list[tuple[int, str]]:
    """Return (area_id, label) for areas that have a physical unit installed.

    Active areas are those where setup.systems.system{n}.type != 'None'.
    """
    setup_systems = device_data.get("setup", {}).get("systems", {})
    areas_data = device_data.get("areas", {})
    active: list[tuple[int, str]] = []
    for i in range(1, 7):
        system = setup_systems.get(f"system{i}", {})
        if system.get("type", "None") != "None":
            label = areas_data.get(f"area{i}", {}).get("label", f"Area {i}")
            active.append((i, label))
    return active


def get_area_mode(device_data: dict[str, Any], area_id: int) -> str:
    """Return the current mode string for an area, stripped of whitespace."""
    raw = device_data.get("areas", {}).get(f"area{area_id}", {}).get("mode", "")
    return raw.strip()
