"""Tests for the SEVI Cloud fan platform."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

from homeassistant.components.fan import DOMAIN as FAN_DOMAIN
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.sevi_cloud.const import (
    CONF_API_KEY,
    DOMAIN,
    MODE_BOOST,
    MODE_FANS_OFF,
    MODE_MANUAL_1,
    MODE_MANUAL_2,
    MODE_MANUAL_3,
)

from .conftest import MOCK_COORDINATOR_DATA, TEST_API_KEY, TEST_DEVICE_ID

CONFIG_DATA = {CONF_API_KEY: TEST_API_KEY}

# Entity IDs: HA prefixes with device name because _attr_has_entity_name=True.
FAN_SCHLAFZIMMER = "fan.test_home_schlafzimmer"
FAN_KINDERZIMMER = "fan.test_home_kinderzimmer"
FAN_WOHNZIMMER = "fan.test_home_wohnzimmer"


async def _setup(hass: HomeAssistant):
    """Set up a loaded config entry; return (entry, mock_client)."""
    entry = MockConfigEntry(domain=DOMAIN, data=CONFIG_DATA)
    entry.add_to_hass(hass)

    with patch("custom_components.sevi_cloud.SeviCloudApiClient") as mock_cls:
        mock_client = mock_cls.return_value
        mock_client.async_get_data = AsyncMock(return_value=MOCK_COORDINATOR_DATA)
        mock_client.async_set_area_mode = AsyncMock(return_value=None)

        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    return entry, mock_client


async def test_fan_entities_created(hass: HomeAssistant) -> None:
    """One fan entity per active area should be registered."""
    await _setup(hass)
    for entity_id in (FAN_SCHLAFZIMMER, FAN_KINDERZIMMER, FAN_WOHNZIMMER):
        state = hass.states.get(entity_id)
        assert state is not None, f"Missing entity: {entity_id}"


async def test_fan_initial_state(hass: HomeAssistant) -> None:
    """Fan is on and shows the correct preset from coordinator data."""
    await _setup(hass)
    state = hass.states.get(FAN_SCHLAFZIMMER)
    assert state.state == "on"
    assert state.attributes["preset_mode"] == MODE_MANUAL_1


async def test_inactive_areas_excluded(hass: HomeAssistant) -> None:
    """Areas 1–3 (type None) must not produce fan entities."""
    await _setup(hass)
    for n in (1, 2, 3):
        assert hass.states.get(f"fan.area_{n}") is None
        assert hass.states.get("fan.kein_name") is None


async def test_turn_off(hass: HomeAssistant) -> None:
    """Calling turn_off should call async_set_area_mode with 'Fans off'."""
    entry, mock_client = await _setup(hass)
    with patch("custom_components.sevi_cloud.SeviCloudApiClient") as mock_cls:
        mock_cls.return_value = mock_client
        await hass.services.async_call(
            FAN_DOMAIN,
            "turn_off",
            {"entity_id": FAN_SCHLAFZIMMER},
            blocking=True,
        )
    mock_client.async_set_area_mode.assert_called_once_with(TEST_DEVICE_ID, 4, MODE_FANS_OFF)


async def test_set_preset_boost(hass: HomeAssistant) -> None:
    """Setting preset_mode to Boost ventilation calls the API."""
    entry, mock_client = await _setup(hass)
    await hass.services.async_call(
        FAN_DOMAIN,
        "set_preset_mode",
        {"entity_id": FAN_SCHLAFZIMMER, "preset_mode": MODE_BOOST},
        blocking=True,
    )
    mock_client.async_set_area_mode.assert_called_once_with(TEST_DEVICE_ID, 4, MODE_BOOST)


async def test_set_percentage(hass: HomeAssistant) -> None:
    """Setting a speed percentage maps to the correct Manual mode."""
    entry, mock_client = await _setup(hass)
    # 33% → Manual 2 (second item in the 6-item ordered list)
    await hass.services.async_call(
        FAN_DOMAIN,
        "set_percentage",
        {"entity_id": FAN_SCHLAFZIMMER, "percentage": 33},
        blocking=True,
    )
    called_mode = mock_client.async_set_area_mode.call_args[0][2]
    assert called_mode in (MODE_MANUAL_2, MODE_MANUAL_3)  # tolerance for rounding
