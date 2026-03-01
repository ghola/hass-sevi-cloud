"""Tests for the SEVI Cloud config flow."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from custom_components.sevi_cloud.api import (
    SeviCloudApiClientAuthenticationError,
    SeviCloudApiClientCommunicationError,
)
from custom_components.sevi_cloud.const import CONF_API_KEY, DOMAIN

USER_INPUT = {CONF_API_KEY: "valid-api-key"}
DEVICE_LIST = [{"deviceid": "933554", "name": "Test Home"}]


async def test_user_form_shown(hass: HomeAssistant) -> None:
    """The user step should show a form with no errors."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {}


async def test_successful_setup(hass: HomeAssistant) -> None:
    """Valid API key creates a config entry."""
    with patch(
        "custom_components.sevi_cloud.config_flow.SeviCloudApiClient.async_authenticate",
        new_callable=AsyncMock,
        return_value=DEVICE_LIST,
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_USER},
            data=USER_INPUT,
        )

    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert result["title"] == "SEVI Cloud"
    assert result["data"] == USER_INPUT


async def test_invalid_auth(hass: HomeAssistant) -> None:
    """An authentication error shows the invalid_auth error."""
    with patch(
        "custom_components.sevi_cloud.config_flow.SeviCloudApiClient.async_authenticate",
        side_effect=SeviCloudApiClientAuthenticationError,
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_USER},
            data=USER_INPUT,
        )

    assert result["type"] == FlowResultType.FORM
    assert result["errors"]["base"] == "invalid_auth"


async def test_cannot_connect(hass: HomeAssistant) -> None:
    """A communication error shows the cannot_connect error."""
    with patch(
        "custom_components.sevi_cloud.config_flow.SeviCloudApiClient.async_authenticate",
        side_effect=SeviCloudApiClientCommunicationError,
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_USER},
            data=USER_INPUT,
        )

    assert result["type"] == FlowResultType.FORM
    assert result["errors"]["base"] == "cannot_connect"


async def test_duplicate_entry_aborted(hass: HomeAssistant) -> None:
    """A second entry for the same devices is aborted."""
    with patch(
        "custom_components.sevi_cloud.config_flow.SeviCloudApiClient.async_authenticate",
        new_callable=AsyncMock,
        return_value=DEVICE_LIST,
    ):
        await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_USER},
            data=USER_INPUT,
        )
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_USER},
            data=USER_INPUT,
        )

    assert result["type"] == FlowResultType.ABORT
    assert result["reason"] == "already_configured"
