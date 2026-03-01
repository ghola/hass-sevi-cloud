"""The SEVI Cloud integration."""

from __future__ import annotations

from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import aiohttp_client
from homeassistant.loader import async_get_loaded_integration

from .api import SeviCloudApiClient
from .const import CONF_API_KEY
from .coordinator import SeviCloudDataUpdateCoordinator
from .data import SeviCloudConfigEntry, SeviCloudData

PLATFORMS: list[Platform] = [
    Platform.FAN,
    Platform.SWITCH,
    Platform.BUTTON,
    Platform.SENSOR,
    Platform.NUMBER,
]


async def async_setup_entry(hass: HomeAssistant, entry: SeviCloudConfigEntry) -> bool:
    """Set up SEVI Cloud from a config entry."""
    client = SeviCloudApiClient(
        api_key=entry.data[CONF_API_KEY],
        session=aiohttp_client.async_get_clientsession(hass),
    )

    coordinator = SeviCloudDataUpdateCoordinator(hass=hass, config_entry=entry)

    entry.runtime_data = SeviCloudData(
        client=client,
        coordinator=coordinator,
        integration=async_get_loaded_integration(hass, entry.domain),
    )

    await coordinator.async_config_entry_first_refresh()
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))

    return True


async def async_unload_entry(hass: HomeAssistant, entry: SeviCloudConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def async_reload_entry(hass: HomeAssistant, entry: SeviCloudConfigEntry) -> None:
    """Reload a config entry when options change."""
    await hass.config_entries.async_reload(entry.entry_id)
