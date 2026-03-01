"""DataUpdateCoordinator for SEVI Cloud."""

from __future__ import annotations

from datetime import timedelta
from typing import TYPE_CHECKING, Any

from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import SeviCloudApiClientAuthenticationError, SeviCloudApiClientError
from .const import DEFAULT_SCAN_INTERVAL, DOMAIN, LOGGER

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

    from .data import SeviCloudConfigEntry


class SeviCloudDataUpdateCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Coordinator that polls the SEVI Cloud API on a schedule."""

    config_entry: SeviCloudConfigEntry

    def __init__(self, hass: HomeAssistant, config_entry: SeviCloudConfigEntry) -> None:
        super().__init__(
            hass,
            LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL),
        )
        self.config_entry = config_entry

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from the SEVI Cloud API."""
        try:
            return await self.config_entry.runtime_data.client.async_get_data()
        except SeviCloudApiClientAuthenticationError as exc:
            raise ConfigEntryAuthFailed(exc) from exc
        except SeviCloudApiClientError as exc:
            raise UpdateFailed(exc) from exc
