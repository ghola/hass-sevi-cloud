"""Config flow for SEVI Cloud integration."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.helpers import selector
from homeassistant.helpers.aiohttp_client import async_create_clientsession

from .api import (
    SeviCloudApiClient,
    SeviCloudApiClientAuthenticationError,
    SeviCloudApiClientCommunicationError,
    SeviCloudApiClientError,
)
from .const import CONF_API_KEY, DOMAIN, LOGGER

STEP_USER_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_API_KEY): selector.TextSelector(
            selector.TextSelectorConfig(type=selector.TextSelectorType.PASSWORD)
        ),
    }
)


class SeviCloudConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for SEVI Cloud."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                devices = await self._validate_api_key(user_input[CONF_API_KEY])
            except SeviCloudApiClientAuthenticationError:
                errors["base"] = "invalid_auth"
            except SeviCloudApiClientCommunicationError:
                errors["base"] = "cannot_connect"
            except SeviCloudApiClientError:
                LOGGER.exception("Unexpected API error during config flow")
                errors["base"] = "unknown"
            else:
                # Use sorted device IDs as a stable unique identifier.
                device_ids = sorted(d["deviceid"] for d in devices)
                unique_id = "_".join(device_ids)
                await self.async_set_unique_id(unique_id)
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title="SEVI Cloud",
                    data=user_input,
                )

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_SCHEMA,
            errors=errors,
        )

    async def async_step_reauth(
        self, entry_data: Mapping[str, Any]
    ) -> config_entries.ConfigFlowResult:
        """Handle re-authentication when the API key becomes invalid."""
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Show the re-authentication form and validate the new key."""
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                await self._validate_api_key(user_input[CONF_API_KEY])
            except SeviCloudApiClientAuthenticationError:
                errors["base"] = "invalid_auth"
            except SeviCloudApiClientCommunicationError:
                errors["base"] = "cannot_connect"
            except SeviCloudApiClientError:
                LOGGER.exception("Unexpected API error during reauth")
                errors["base"] = "unknown"
            else:
                return self.async_update_reload_and_abort(
                    self._get_reauth_entry(),
                    data_updates={CONF_API_KEY: user_input[CONF_API_KEY]},
                )

        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=STEP_USER_SCHEMA,
            errors=errors,
        )

    async def _validate_api_key(self, api_key: str) -> list[dict[str, Any]]:
        """Create a client and call GET /devices to validate the API key."""
        client = SeviCloudApiClient(
            api_key=api_key,
            session=async_create_clientsession(self.hass),
        )
        return await client.async_authenticate()
