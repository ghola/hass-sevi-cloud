"""Constants for the SEVI Cloud integration."""

from __future__ import annotations

import logging
from typing import Final

DOMAIN: Final = "sevi_cloud"

LOGGER = logging.getLogger(__package__)

CONF_API_KEY: Final = "api_key"

API_BASE_URL: Final = "https://api.sec-smart.app/v1"
DEFAULT_SCAN_INTERVAL: Final = 60  # seconds

# Ventilation area mode strings exactly as returned/accepted by the API.
MODE_FANS_OFF: Final = "Fans off"
MODE_MANUAL_1: Final = "Manual 1"
MODE_MANUAL_2: Final = "Manual 2"
MODE_MANUAL_3: Final = "Manual 3"
MODE_MANUAL_4: Final = "Manual 4"
MODE_MANUAL_5: Final = "Manual 5"
MODE_MANUAL_6: Final = "Manual 6"
MODE_BOOST: Final = "Boost ventilation"
MODE_HUMIDITY: Final = "Humidity regulation"
MODE_CO2: Final = "CO2 regulation"
MODE_TIMED: Final = "Timed program"
MODE_INACTIVE: Final = "INACTIVE"

MANUAL_MODES: Final = (
    MODE_MANUAL_1,
    MODE_MANUAL_2,
    MODE_MANUAL_3,
    MODE_MANUAL_4,
    MODE_MANUAL_5,
    MODE_MANUAL_6,
)

# Preset modes exposed on the fan entity.
FAN_PRESET_MODES: Final = list(MANUAL_MODES) + [
    MODE_BOOST,
    MODE_HUMIDITY,
    MODE_CO2,
]

# Speed level → percentage (1/6 … 6/6, rounded).
SPEED_TO_PCT: Final[dict[str, int]] = {
    MODE_MANUAL_1: 17,
    MODE_MANUAL_2: 33,
    MODE_MANUAL_3: 50,
    MODE_MANUAL_4: 67,
    MODE_MANUAL_5: 83,
    MODE_MANUAL_6: 100,
}
