"""Pytest configuration and shared fixtures for SEVI Cloud tests."""

from __future__ import annotations

import os
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.sevi_cloud.api import SeviCloudApiClient
from custom_components.sevi_cloud.const import CONF_API_KEY, DOMAIN

pytest_plugins = "pytest_homeassistant_custom_component"

# ---------------------------------------------------------------------------
# Load .env if present (never committed — see .env.example)
# ---------------------------------------------------------------------------

_dotenv_path = Path(__file__).parent.parent / ".env"
if _dotenv_path.exists():
    for _line in _dotenv_path.read_text().splitlines():
        _line = _line.strip()
        if _line and not _line.startswith("#") and "=" in _line:
            _key, _, _val = _line.partition("=")
            os.environ.setdefault(_key.strip(), _val.strip())

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

TEST_API_KEY = "test-api-key-1234"
TEST_DEVICE_ID = "933554"

# Minimal device payload that mirrors the real API response.
MOCK_DEVICE_DATA = {
    "id": TEST_DEVICE_ID,
    "name": "Test Home",
    "areas": {
        "area1": {"label": "Kein Name", "mode": "INACTIVE "},
        "area2": {"label": "Kein Name", "mode": "INACTIVE "},
        "area3": {"label": "Kein Name", "mode": "INACTIVE "},
        "area4": {"label": "Schlafzimmer", "mode": "Manual 1"},
        "area5": {"label": "Kinderzimmer", "mode": "Manual 2"},
        "area6": {"label": "Wohnzimmer", "mode": "Manual 1"},
    },
    "telemetry": {
        "restFilterTime": 42,
        "restSleepTime": {"area4": 60, "area5": 60, "area6": 60},
        "co2": 0,
        "humidity": 0,
    },
    "settings": {
        "filter": {"maxRunTime": 180},
        "deviceTime": {"time": "09:00", "date": "2025-03-08", "autoSynch": True},
        "summermode": False,
    },
    "setup": {
        "systems": {
            "system1": {"type": "None", "installed": "Area 1"},
            "system2": {"type": "None", "installed": "Area 2"},
            "system3": {"type": "None", "installed": "Area 3"},
            "system4": {"type": "SEVi160", "installed": "Area 4"},
            "system5": {"type": "SEVi160", "installed": "Area 5"},
            "system6": {"type": "SEVi160", "installed": "Area 6"},
        },
        "areas": {
            "area1": "Supply and exhaust air",
            "area2": "Supply and exhaust air",
            "area3": "Supply and exhaust air",
            "area4": "Supply and exhaust air",
            "area5": "Supply and exhaust air",
            "area6": "Supply and exhaust air",
        },
    },
}

# Coordinator data: device_id → full device dict.
MOCK_COORDINATOR_DATA = {TEST_DEVICE_ID: MOCK_DEVICE_DATA}


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Enable custom integrations for every test in this suite."""
    return enable_custom_integrations


# ---------------------------------------------------------------------------
# Config entry
# ---------------------------------------------------------------------------


@pytest.fixture
def config_entry_data() -> dict:
    """Return sample config entry data."""
    return {CONF_API_KEY: TEST_API_KEY}


@pytest.fixture
def mock_config_entry(config_entry_data: dict) -> MockConfigEntry:
    """Return an unpersisted MockConfigEntry."""
    return MockConfigEntry(domain=DOMAIN, data=config_entry_data, title="SEVI Cloud")


# ---------------------------------------------------------------------------
# API client mock
# ---------------------------------------------------------------------------


@pytest.fixture
def real_api_key() -> str:
    """Return the real API key from the environment, or skip the test.

    Set SEVI_API_KEY in your shell or in a gitignored .env file
    (copy .env.example → .env and fill in your key).
    """
    key = os.environ.get("SEVI_API_KEY", "")
    if not key or key == "your-api-key-here":
        pytest.skip("SEVI_API_KEY not set — skipping live test (see .env.example)")
    return key


@pytest.fixture
def mock_api_client() -> MagicMock:
    """Return a mock SeviCloudApiClient with realistic default responses."""
    client = MagicMock(spec=SeviCloudApiClient)
    client.async_authenticate = AsyncMock(
        return_value=[{"deviceid": TEST_DEVICE_ID, "name": "Test Home"}]
    )
    client.async_get_data = AsyncMock(return_value=MOCK_COORDINATOR_DATA)
    client.async_set_area_mode = AsyncMock(return_value=None)
    client.async_set_summer_mode = AsyncMock(return_value=None)
    client.async_set_filter_max_runtime = AsyncMock(return_value=None)
    client.async_reset_filter = AsyncMock(return_value=None)
    client.async_set_device_time_autosync = AsyncMock(return_value=None)
    return client
