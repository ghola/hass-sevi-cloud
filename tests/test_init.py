"""Tests for SEVI Cloud integration setup and teardown."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.sevi_cloud.const import CONF_API_KEY, DOMAIN

from .conftest import MOCK_COORDINATOR_DATA, TEST_API_KEY

CONFIG_DATA = {CONF_API_KEY: TEST_API_KEY}


def _mock_entry(hass: HomeAssistant) -> MockConfigEntry:
    entry = MockConfigEntry(domain=DOMAIN, data=CONFIG_DATA)
    entry.add_to_hass(hass)
    return entry


async def test_setup_entry(hass: HomeAssistant) -> None:
    """Integration loads successfully when the API returns data."""
    entry = _mock_entry(hass)
    with patch("custom_components.sevi_cloud.SeviCloudApiClient") as mock_cls:
        mock_cls.return_value.async_get_data = AsyncMock(return_value=MOCK_COORDINATOR_DATA)

        result = await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

        assert result is True
        assert entry.state is ConfigEntryState.LOADED


async def test_unload_entry(hass: HomeAssistant) -> None:
    """Integration unloads cleanly."""
    entry = _mock_entry(hass)
    with patch(
        "custom_components.sevi_cloud.SeviCloudApiClient",
    ) as mock_cls:
        mock_cls.return_value.async_get_data = AsyncMock(return_value=MOCK_COORDINATOR_DATA)

        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

        result = await hass.config_entries.async_unload(entry.entry_id)
        await hass.async_block_till_done()

    assert result is True
    assert entry.state is ConfigEntryState.NOT_LOADED
