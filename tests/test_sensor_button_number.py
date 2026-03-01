"""Tests for sensor, button, and number platforms."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

from homeassistant.components.button import DOMAIN as BUTTON_DOMAIN
from homeassistant.components.number import DOMAIN as NUMBER_DOMAIN
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.sevi_cloud.const import CONF_API_KEY, DOMAIN

from .conftest import MOCK_COORDINATOR_DATA, TEST_API_KEY, TEST_DEVICE_ID

CONFIG_DATA = {CONF_API_KEY: TEST_API_KEY}


async def _setup(hass: HomeAssistant):
    entry = MockConfigEntry(domain=DOMAIN, data=CONFIG_DATA)
    entry.add_to_hass(hass)

    with patch("custom_components.sevi_cloud.SeviCloudApiClient") as mock_cls:
        mock_client = mock_cls.return_value
        mock_client.async_get_data = AsyncMock(return_value=MOCK_COORDINATOR_DATA)
        mock_client.async_reset_filter = AsyncMock(return_value=None)
        mock_client.async_set_filter_max_runtime = AsyncMock(return_value=None)

        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    return entry, mock_client


# ---------------------------------------------------------------------------
# Sensor: filter remaining
# ---------------------------------------------------------------------------


async def test_filter_remaining_sensor_created(hass: HomeAssistant) -> None:
    await _setup(hass)
    state = hass.states.get("sensor.test_home_filter_remaining")
    assert state is not None


async def test_filter_remaining_value(hass: HomeAssistant) -> None:
    """Sensor shows restFilterTime from telemetry (42 days in fixture)."""
    await _setup(hass)
    state = hass.states.get("sensor.test_home_filter_remaining")
    assert state.state == "42"
    assert state.attributes["unit_of_measurement"] == "d"


# ---------------------------------------------------------------------------
# Button: filter reset
# ---------------------------------------------------------------------------


async def test_filter_reset_button_created(hass: HomeAssistant) -> None:
    await _setup(hass)
    assert hass.states.get("button.test_home_reset_filter") is not None


async def test_filter_reset_button_press(hass: HomeAssistant) -> None:
    """Pressing the reset button calls async_reset_filter."""
    entry, mock_client = await _setup(hass)
    await hass.services.async_call(
        BUTTON_DOMAIN,
        "press",
        {"entity_id": "button.test_home_reset_filter"},
        blocking=True,
    )
    mock_client.async_reset_filter.assert_called_once_with(TEST_DEVICE_ID)


# ---------------------------------------------------------------------------
# Number: filter max runtime
# ---------------------------------------------------------------------------


async def test_filter_max_runtime_number_created(hass: HomeAssistant) -> None:
    await _setup(hass)
    assert hass.states.get("number.test_home_filter_replacement_interval") is not None


async def test_filter_max_runtime_value(hass: HomeAssistant) -> None:
    """Number shows maxRunTime from settings (180 in fixture)."""
    await _setup(hass)
    state = hass.states.get("number.test_home_filter_replacement_interval")
    assert state.state == "180"


async def test_filter_max_runtime_set_value(hass: HomeAssistant) -> None:
    """Setting the number calls async_set_filter_max_runtime."""
    entry, mock_client = await _setup(hass)
    await hass.services.async_call(
        NUMBER_DOMAIN,
        "set_value",
        {
            "entity_id": "number.test_home_filter_replacement_interval",
            "value": 270,
        },
        blocking=True,
    )
    mock_client.async_set_filter_max_runtime.assert_called_once_with(TEST_DEVICE_ID, 270)
