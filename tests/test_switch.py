"""Tests for the SEVI Cloud switch platform."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

from homeassistant.components.switch import DOMAIN as SWITCH_DOMAIN
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.sevi_cloud.const import CONF_API_KEY, DOMAIN, MODE_BOOST, MODE_MANUAL_1

from .conftest import MOCK_COORDINATOR_DATA, TEST_API_KEY, TEST_DEVICE_ID

CONFIG_DATA = {CONF_API_KEY: TEST_API_KEY}


async def _setup(hass: HomeAssistant):
    entry = MockConfigEntry(domain=DOMAIN, data=CONFIG_DATA)
    entry.add_to_hass(hass)

    with patch("custom_components.sevi_cloud.SeviCloudApiClient") as mock_cls:
        mock_client = mock_cls.return_value
        mock_client.async_get_data = AsyncMock(return_value=MOCK_COORDINATOR_DATA)
        mock_client.async_set_area_mode = AsyncMock(return_value=None)
        mock_client.async_set_summer_mode = AsyncMock(return_value=None)
        mock_client.async_set_device_time_autosync = AsyncMock(return_value=None)

        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    return entry, mock_client


# ---------------------------------------------------------------------------
# Boost switches
# ---------------------------------------------------------------------------


async def test_boost_switches_created(hass: HomeAssistant) -> None:
    """One boost switch per active area (entity IDs prefixed with device name)."""
    await _setup(hass)
    for label in ("bedroom_boost", "kids_room_boost", "living_room_boost"):
        state = hass.states.get(f"switch.test_home_{label}")
        assert state is not None, f"Missing switch.test_home_{label}"


async def test_boost_initial_state_off(hass: HomeAssistant) -> None:
    """Boost switch is off when current mode is not Boost ventilation."""
    await _setup(hass)
    state = hass.states.get("switch.test_home_bedroom_boost")
    assert state.state == "off"


async def test_boost_turn_on(hass: HomeAssistant) -> None:
    """Turning on boost sets area mode to 'Boost ventilation'."""
    entry, mock_client = await _setup(hass)
    await hass.services.async_call(
        SWITCH_DOMAIN,
        "turn_on",
        {"entity_id": "switch.test_home_bedroom_boost"},
        blocking=True,
    )
    mock_client.async_set_area_mode.assert_called_once_with(TEST_DEVICE_ID, 4, MODE_BOOST)


async def test_boost_turn_off(hass: HomeAssistant) -> None:
    """Turning off boost restores area mode to Manual 1."""
    entry, mock_client = await _setup(hass)
    await hass.services.async_call(
        SWITCH_DOMAIN,
        "turn_off",
        {"entity_id": "switch.test_home_bedroom_boost"},
        blocking=True,
    )
    mock_client.async_set_area_mode.assert_called_once_with(TEST_DEVICE_ID, 4, MODE_MANUAL_1)


# ---------------------------------------------------------------------------
# Summer mode switch
# ---------------------------------------------------------------------------


async def test_summer_mode_switch_created(hass: HomeAssistant) -> None:
    await _setup(hass)
    assert hass.states.get("switch.test_home_summer_mode") is not None


async def test_summer_mode_initial_off(hass: HomeAssistant) -> None:
    """Summer mode is off per test device data (summermode: false)."""
    await _setup(hass)
    state = hass.states.get("switch.test_home_summer_mode")
    assert state.state == "off"


async def test_summer_mode_turn_on(hass: HomeAssistant) -> None:
    entry, mock_client = await _setup(hass)
    await hass.services.async_call(
        SWITCH_DOMAIN,
        "turn_on",
        {"entity_id": "switch.test_home_summer_mode"},
        blocking=True,
    )
    mock_client.async_set_summer_mode.assert_called_once_with(TEST_DEVICE_ID, enabled=True)


# ---------------------------------------------------------------------------
# Time auto-sync switch
# ---------------------------------------------------------------------------


async def test_time_autosync_switch_created(hass: HomeAssistant) -> None:
    await _setup(hass)
    assert hass.states.get("switch.test_home_time_auto_sync") is not None


async def test_time_autosync_initial_on(hass: HomeAssistant) -> None:
    """Auto-sync is on per test device data (autoSynch: true)."""
    await _setup(hass)
    state = hass.states.get("switch.test_home_time_auto_sync")
    assert state.state == "on"


async def test_time_autosync_turn_off(hass: HomeAssistant) -> None:
    entry, mock_client = await _setup(hass)
    await hass.services.async_call(
        SWITCH_DOMAIN,
        "turn_off",
        {"entity_id": "switch.test_home_time_auto_sync"},
        blocking=True,
    )
    mock_client.async_set_device_time_autosync.assert_called_once_with(
        TEST_DEVICE_ID, enabled=False
    )
