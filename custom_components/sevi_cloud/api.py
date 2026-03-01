"""REST API client for the SEC Smart / SEVI Cloud API."""

from __future__ import annotations

import asyncio
import json
from typing import Any

import aiohttp

from .const import API_BASE_URL


class SeviCloudApiClientError(Exception):
    """Base exception for API errors."""


class SeviCloudApiClientAuthenticationError(SeviCloudApiClientError):
    """Raised on HTTP 401 / 403 responses."""


class SeviCloudApiClientCommunicationError(SeviCloudApiClientError):
    """Raised on network timeouts or unexpected HTTP status codes."""


class SeviCloudApiClient:
    """Async client for the SEC Smart API."""

    def __init__(
        self,
        api_key: str,
        session: aiohttp.ClientSession,
        base_url: str = API_BASE_URL,
    ) -> None:
        self._api_key = api_key
        self._session = session
        self._base_url = base_url.rstrip("/")

    # ------------------------------------------------------------------
    # High-level helpers used by the coordinator / config flow
    # ------------------------------------------------------------------

    async def async_authenticate(self) -> list[dict[str, Any]]:
        """Validate the API key by listing devices.

        Returns the raw device list so the config flow can derive a unique ID.
        Raises SeviCloudApiClientAuthenticationError on invalid key.
        """
        return await self._request("GET", "/devices")

    async def async_get_data(self) -> dict[str, Any]:
        """Fetch the full state for every device the key has access to.

        Returns a mapping of device_id -> full device dict.
        """
        devices = await self._request("GET", "/devices")
        result: dict[str, Any] = {}
        for entry in devices:
            device_id = entry["deviceid"]
            result[device_id] = await self._request("GET", f"/devices/{device_id}")
        return result

    # ------------------------------------------------------------------
    # Area / ventilation control
    # ------------------------------------------------------------------

    async def async_set_area_mode(self, device_id: str, area_id: int, mode: str) -> None:
        """Set the ventilation mode for a specific area (1-6)."""
        await self._request(
            "PUT",
            f"/devices/{device_id}/areas/mode",
            json={"areaid": area_id, "mode": mode},
        )

    # ------------------------------------------------------------------
    # Settings
    # ------------------------------------------------------------------

    async def async_set_summer_mode(self, device_id: str, *, enabled: bool) -> None:
        """Enable or disable summer ventilation mode."""
        await self._request(
            "PUT",
            f"/devices/{device_id}/settings/summermode",
            json={"summermode": enabled},
        )

    async def async_set_filter_max_runtime(self, device_id: str, days: int) -> None:
        """Set the filter replacement interval (90-270 days)."""
        await self._request(
            "PUT",
            f"/devices/{device_id}/settings/filter",
            json={"filter": {"maxRunTime": days}},
        )

    async def async_reset_filter(self, device_id: str) -> None:
        """Mark the filter as replaced (resets the runtime counter)."""
        await self._request(
            "PUT",
            f"/devices/{device_id}/settings/filter",
            json={"filter": {"reset": True}},
        )

    async def async_set_device_time_autosync(self, device_id: str, *, enabled: bool) -> None:
        """Enable or disable automatic time synchronisation."""
        await self._request(
            "PUT",
            f"/devices/{device_id}/settings/device-time",
            json={"deviceTime": {"autoSynch": enabled}},
        )

    # ------------------------------------------------------------------
    # Internal HTTP helper
    # ------------------------------------------------------------------

    async def _request(
        self,
        method: str,
        endpoint: str,
        **kwargs: Any,
    ) -> Any:
        """Execute an authenticated HTTP request and return parsed JSON."""
        url = f"{self._base_url}{endpoint}"
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            **kwargs.pop("headers", {}),
        }
        try:
            async with asyncio.timeout(15):
                response = await self._session.request(method, url, headers=headers, **kwargs)
        except TimeoutError as exc:
            raise SeviCloudApiClientCommunicationError(f"Timeout reaching {url}") from exc
        except aiohttp.ClientError as exc:
            raise SeviCloudApiClientCommunicationError(
                f"Network error reaching {url}: {exc}"
            ) from exc

        if response.status in (401, 403):
            raise SeviCloudApiClientAuthenticationError(
                f"Authentication failed (HTTP {response.status})"
            )
        if not response.ok:
            raise SeviCloudApiClientCommunicationError(
                f"Unexpected HTTP {response.status} from {url}"
            )

        # GET endpoints return JSON; PUT endpoints return empty or plain-text bodies.
        text = await response.text()
        if not text.strip():
            return {}
        try:
            return json.loads(text)
        except ValueError:
            return {}
