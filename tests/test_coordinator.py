"""Tests for the SEVI Cloud DataUpdateCoordinator."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.sevi_cloud.api import (
    SeviCloudApiClientAuthenticationError,
    SeviCloudApiClientCommunicationError,
)
from custom_components.sevi_cloud.const import CONF_API_KEY, DOMAIN
from custom_components.sevi_cloud.coordinator import SeviCloudDataUpdateCoordinator

from .conftest import MOCK_COORDINATOR_DATA, TEST_API_KEY

CONFIG_DATA = {CONF_API_KEY: TEST_API_KEY}


async def test_coordinator_update_success(hass: HomeAssistant) -> None:
    """Coordinator stores returned data after a successful API call."""
    entry = MockConfigEntry(domain=DOMAIN, data=CONFIG_DATA)
    entry.add_to_hass(hass)

    with patch("custom_components.sevi_cloud.SeviCloudApiClient") as mock_cls:
        mock_client = mock_cls.return_value
        mock_client.async_get_data = AsyncMock(return_value=MOCK_COORDINATOR_DATA)

        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

        coordinator: SeviCloudDataUpdateCoordinator = entry.runtime_data.coordinator
        assert coordinator.data == MOCK_COORDINATOR_DATA


async def test_coordinator_auth_failure(hass: HomeAssistant) -> None:
    """An auth error on first refresh sets entry to SETUP_ERROR."""
    entry = MockConfigEntry(domain=DOMAIN, data=CONFIG_DATA)
    entry.add_to_hass(hass)

    with patch("custom_components.sevi_cloud.SeviCloudApiClient") as mock_cls:
        mock_cls.return_value.async_get_data = AsyncMock(
            side_effect=SeviCloudApiClientAuthenticationError("bad key")
        )
        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

        assert entry.state is ConfigEntryState.SETUP_ERROR


async def test_coordinator_communication_failure(hass: HomeAssistant) -> None:
    """A comms error on first refresh sets entry to SETUP_RETRY."""
    entry = MockConfigEntry(domain=DOMAIN, data=CONFIG_DATA)
    entry.add_to_hass(hass)

    with patch("custom_components.sevi_cloud.SeviCloudApiClient") as mock_cls:
        mock_cls.return_value.async_get_data = AsyncMock(
            side_effect=SeviCloudApiClientCommunicationError("timeout")
        )
        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

        assert entry.state is ConfigEntryState.SETUP_RETRY
