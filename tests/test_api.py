"""Tests for the SEVI Cloud API client."""

from __future__ import annotations

import aiohttp
import pytest
from aioresponses import aioresponses
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from custom_components.sevi_cloud.api import (
    SeviCloudApiClient,
    SeviCloudApiClientAuthenticationError,
    SeviCloudApiClientCommunicationError,
)
from custom_components.sevi_cloud.const import API_BASE_URL

API_KEY = "test-key"


@pytest.fixture
async def client(hass: HomeAssistant) -> SeviCloudApiClient:
    """Return a real client wired to HA's aiohttp session."""
    return SeviCloudApiClient(
        api_key=API_KEY,
        session=async_get_clientsession(hass),
    )


# ---------------------------------------------------------------------------
# HTTP error handling
# ---------------------------------------------------------------------------


async def test_request_401_raises_auth_error(client: SeviCloudApiClient) -> None:
    with aioresponses() as m:
        m.get(f"{API_BASE_URL}/devices", status=401)
        with pytest.raises(SeviCloudApiClientAuthenticationError):
            await client._request("GET", "/devices")


async def test_request_403_raises_auth_error(client: SeviCloudApiClient) -> None:
    with aioresponses() as m:
        m.get(f"{API_BASE_URL}/devices", status=403)
        with pytest.raises(SeviCloudApiClientAuthenticationError):
            await client._request("GET", "/devices")


async def test_request_500_raises_comms_error(client: SeviCloudApiClient) -> None:
    with aioresponses() as m:
        m.get(f"{API_BASE_URL}/devices", status=500)
        with pytest.raises(SeviCloudApiClientCommunicationError):
            await client._request("GET", "/devices")


async def test_request_timeout_raises_comms_error(client: SeviCloudApiClient) -> None:
    with aioresponses() as m:
        m.get(f"{API_BASE_URL}/devices", exception=TimeoutError())
        with pytest.raises(SeviCloudApiClientCommunicationError):
            await client._request("GET", "/devices")


async def test_request_client_error_raises_comms_error(
    client: SeviCloudApiClient,
) -> None:
    with aioresponses() as m:
        m.get(f"{API_BASE_URL}/devices", exception=aiohttp.ClientError("boom"))
        with pytest.raises(SeviCloudApiClientCommunicationError):
            await client._request("GET", "/devices")


# ---------------------------------------------------------------------------
# authenticate
# ---------------------------------------------------------------------------


async def test_authenticate_returns_device_list(client: SeviCloudApiClient) -> None:
    payload = [{"deviceid": "933554", "name": "Acasa"}]
    with aioresponses() as m:
        m.get(f"{API_BASE_URL}/devices", payload=payload)
        result = await client.async_authenticate()
    assert result == payload


async def test_authenticate_raises_on_invalid_key(client: SeviCloudApiClient) -> None:
    with aioresponses() as m:
        m.get(f"{API_BASE_URL}/devices", status=401)
        with pytest.raises(SeviCloudApiClientAuthenticationError):
            await client.async_authenticate()


# ---------------------------------------------------------------------------
# get_data
# ---------------------------------------------------------------------------


async def test_get_data_fetches_all_devices(client: SeviCloudApiClient) -> None:
    device_list = [{"deviceid": "123"}, {"deviceid": "456"}]
    device_123 = {"id": "123", "name": "Dev A"}
    device_456 = {"id": "456", "name": "Dev B"}
    with aioresponses() as m:
        m.get(f"{API_BASE_URL}/devices", payload=device_list)
        m.get(f"{API_BASE_URL}/devices/123", payload=device_123)
        m.get(f"{API_BASE_URL}/devices/456", payload=device_456)
        result = await client.async_get_data()
    assert result == {"123": device_123, "456": device_456}


# ---------------------------------------------------------------------------
# Write commands (smoke tests via mocked HTTP)
# ---------------------------------------------------------------------------


async def test_set_area_mode(client: SeviCloudApiClient) -> None:
    with aioresponses() as m:
        m.put(f"{API_BASE_URL}/devices/933554/areas/mode", body="")
        await client.async_set_area_mode("933554", 4, "Boost ventilation")


async def test_set_summer_mode(client: SeviCloudApiClient) -> None:
    with aioresponses() as m:
        m.put(f"{API_BASE_URL}/devices/933554/settings/summermode", body="")
        await client.async_set_summer_mode("933554", enabled=True)


async def test_reset_filter(client: SeviCloudApiClient) -> None:
    with aioresponses() as m:
        m.put(f"{API_BASE_URL}/devices/933554/settings/filter", body="")
        await client.async_reset_filter("933554")


async def test_set_filter_max_runtime(client: SeviCloudApiClient) -> None:
    with aioresponses() as m:
        m.put(f"{API_BASE_URL}/devices/933554/settings/filter", body="")
        await client.async_set_filter_max_runtime("933554", 180)


async def test_set_device_time_autosync(client: SeviCloudApiClient) -> None:
    with aioresponses() as m:
        m.put(f"{API_BASE_URL}/devices/933554/settings/device-time", body="")
        await client.async_set_device_time_autosync("933554", enabled=False)


async def test_write_with_plain_text_response_does_not_raise(
    client: SeviCloudApiClient,
) -> None:
    """PUT endpoints that return plain text (e.g. 'OK') must not raise."""
    with aioresponses() as m:
        m.put(f"{API_BASE_URL}/devices/933554/areas/mode", body="OK")
        await client.async_set_area_mode("933554", 4, "Boost ventilation")
