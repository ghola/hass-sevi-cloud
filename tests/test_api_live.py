"""Live integration tests — hit the real SEC Smart API.

These tests are skipped unless SEVI_API_KEY is set in the environment
or in a gitignored .env file (copy .env.example → .env).

Run only live tests:
    pytest -m live -v

Skip live tests (default CI behaviour):
    pytest -m "not live"   # or just: pytest   (live tests auto-skip without the key)
"""

from __future__ import annotations

import aiohttp
import pytest

from custom_components.sevi_cloud.api import SeviCloudApiClient


@pytest.fixture
async def live_client(real_api_key: str) -> SeviCloudApiClient:
    """Return a real SeviCloudApiClient using the key from .env / env var."""
    async with aiohttp.ClientSession() as session:
        yield SeviCloudApiClient(api_key=real_api_key, session=session)


# ---------------------------------------------------------------------------
# Authentication / device listing
# ---------------------------------------------------------------------------


@pytest.mark.live
async def test_live_authenticate(live_client: SeviCloudApiClient) -> None:
    """GET /devices returns a non-empty list of devices."""
    devices = await live_client.async_authenticate()
    assert isinstance(devices, list)
    assert len(devices) > 0
    # Each entry must have a device ID.
    assert all("deviceid" in d for d in devices)


# ---------------------------------------------------------------------------
# Full data fetch
# ---------------------------------------------------------------------------


@pytest.mark.live
async def test_live_get_data(live_client: SeviCloudApiClient) -> None:
    """async_get_data returns a non-empty dict keyed by device ID."""
    data = await live_client.async_get_data()
    assert isinstance(data, dict)
    assert len(data) > 0
    # Each device dict must have expected top-level keys.
    for device_id, device_data in data.items():
        assert isinstance(device_id, str)
        assert "areas" in device_data, f"Device {device_id} missing 'areas'"
        assert "settings" in device_data, f"Device {device_id} missing 'settings'"
        assert "telemetry" in device_data, f"Device {device_id} missing 'telemetry'"
        assert "setup" in device_data, f"Device {device_id} missing 'setup'"


@pytest.mark.live
async def test_live_active_areas(live_client: SeviCloudApiClient) -> None:
    """Active areas have a non-empty label and a recognised mode string."""
    from custom_components.sevi_cloud.data import get_active_areas, get_area_mode

    data = await live_client.async_get_data()
    for device_id, device_data in data.items():
        active = get_active_areas(device_data)
        assert len(active) > 0, f"Device {device_id} has no active areas"
        for area_id, label in active:
            assert label, f"Device {device_id} area {area_id} has empty label"
            mode = get_area_mode(device_data, area_id)
            assert mode, f"Device {device_id} area {area_id} has empty mode"
