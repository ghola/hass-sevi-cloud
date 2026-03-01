# hass-sevi-cloud

SEVI ventilation system integration for Home Assistant, installable via [HACS](https://hacs.xyz/).

Communicates with the **SEC Smart cloud API** (`api.sec-smart.app`) using your personal API key.

---

## Table of Contents

- [Supported Features](#supported-features)
- [Not Supported](#not-supported)
- [Installation (end users)](#installation-end-users)
- [Developer Setup](#developer-setup)
- [Project Structure](#project-structure)
- [Running Tests](#running-tests)
- [Testing Against the Real API](#testing-against-the-real-api)
- [Architecture Overview](#architecture-overview)
- [Publishing to HACS](#publishing-to-hacs)
- [Contributing](#contributing)

---

## Supported Features

The integration creates entities automatically based on what the API reports for your device. Areas (rooms) that have no physical unit installed are silently skipped.

### Per ventilation area (room)

| Entity | Type | Description |
|---|---|---|
| `fan.<device>_<room>` | Fan | Ventilation speed — Manual 1–6, Boost, Humidity, CO₂ presets; also exposes a 0–100 % percentage slider mapped to Manual 1–6 |
| `switch.<device>_<room>_boost` | Switch | Shortcut to activate / deactivate Boost ventilation for one room |

### Per device

| Entity | Type | Description |
|---|---|---|
| `switch.<device>_summer_mode` | Switch | Enable / disable summer ventilation (bypasses heat recovery) |
| `switch.<device>_time_auto_sync` | Switch | Enable / disable automatic clock synchronisation |
| `sensor.<device>_filter_remaining` | Sensor | Days remaining before the air filter needs replacing |
| `button.<device>_reset_filter` | Button | Mark the filter as replaced (resets the runtime counter) |
| `number.<device>_filter_replacement_interval` | Number | Maximum filter runtime in days (90 – 270) |

---

## Not Supported

The following API features exist but are intentionally out of scope for this integration:

- **Snooze** — temporary manual overrides with a timer
- **Time programmes** — scheduled ventilation speed changes
- **CO₂ threshold** — automatic speed changes based on CO₂ level
- **Humidity threshold** — automatic speed changes based on relative humidity

---

## Installation (end users)

### Prerequisites

You need a **SEVI Cloud API key**. Obtain it from your SEVI / SEC Smart account or support.

### HACS (recommended)

1. Open HACS in your Home Assistant instance.
2. Go to **Integrations → ⋮ → Custom repositories**.
3. Add this repository URL with category **Integration**.
4. Search for **SEVI Cloud** and click **Download**.
5. Restart Home Assistant.
6. Go to **Settings → Devices & Services → Add Integration** and search for **SEVI Cloud**.
7. Enter your API key and complete the setup.

### Manual

1. Copy `custom_components/sevi_cloud/` into your HA `config/custom_components/` directory.
2. Restart Home Assistant.
3. Follow steps 6–7 above.

---

## Developer Setup

### Prerequisites

- Python 3.13 (the project pins to `3.13.3` via [pyenv](https://github.com/pyenv/pyenv))
- `make` (optional but convenient)
- Git

### Clone and create a virtual environment

```bash
git clone https://github.com/your-org/hass-sevi-cloud.git
cd hass-sevi-cloud

make install
# or manually:
PYENV_VERSION=3.13.3 python3 -m venv .venv
.venv/bin/pip install --upgrade pip
.venv/bin/pip install -r requirements_test.txt
```

The virtual environment is created at `.venv/` and is excluded from version control.

---

## Project Structure

```
hass-sevi-cloud/
│
├── custom_components/
│   └── sevi_cloud/                   # Home Assistant integration package
│       ├── __init__.py               # Entry setup, unload, and reload hooks
│       ├── api.py                    # REST API client (SeviCloudApiClient)
│       ├── button.py                 # Button platform — filter reset per device
│       ├── config_flow.py            # UI configuration flow (API key)
│       ├── const.py                  # Constants: DOMAIN, API base URL, mode strings
│       ├── coordinator.py            # DataUpdateCoordinator — polls API every 60 s
│       ├── data.py                   # SeviCloudData dataclass, helpers (get_active_areas …)
│       ├── entity.py                 # SeviCloudDeviceEntity and SeviCloudAreaEntity bases
│       ├── fan.py                    # Fan platform — ventilation speed per area
│       ├── manifest.json             # Integration metadata (domain, version, iot_class …)
│       ├── number.py                 # Number platform — filter max runtime per device
│       ├── sensor.py                 # Sensor platform — filter remaining days per device
│       ├── strings.json              # UI strings (source of truth)
│       ├── switch.py                 # Switch platform — boost, summer mode, time auto-sync
│       └── translations/
│           └── en.json               # English translations
│
├── tests/
│   ├── conftest.py                   # Shared fixtures, mock API data, TEST_API_KEY constant
│   ├── test_api.py                   # Unit tests for the HTTP client (13 tests)
│   ├── test_config_flow.py           # Config flow UI tests (5 tests)
│   ├── test_coordinator.py           # Coordinator data fetch and error-state tests (3 tests)
│   ├── test_fan.py                   # Fan entity creation and command tests (6 tests)
│   ├── test_init.py                  # Integration setup / unload lifecycle tests (2 tests)
│   ├── test_sensor_button_number.py  # Sensor, button, and number tests (6 tests)
│   └── test_switch.py                # Switch entity tests (9 tests)
│
├── .github/
│   └── workflows/
│       ├── lint.yml                  # Ruff lint + format check on every PR/push
│       ├── tests.yml                 # pytest on every PR/push
│       └── validate.yml              # Hassfest + HACS validation (daily + main branch)
│
├── .ruff.toml                        # Ruff linter configuration
├── hacs.json                         # HACS metadata
├── Makefile                          # Developer shortcuts
├── openapi.json                      # SEC Smart API OpenAPI schema (reference)
├── pyproject.toml                    # pytest and coverage configuration
└── requirements_test.txt             # Test-only Python dependencies
```

---

## Running Tests

```bash
# Run the full test suite with coverage
make test

# Lint only
make lint

# Lint + format check + full test suite
make check

# Or call pytest directly
.venv/bin/pytest tests/ -v
```

The `Makefile` will automatically create the virtual environment and install dependencies if they are missing.

### What is tested

| File | Tests | Covers |
|---|---|---|
| `test_api.py` | 13 | HTTP 401/403/5xx, timeout, `ClientError`, all write commands |
| `test_config_flow.py` | 5 | Happy path, invalid key, connection failure, duplicate-entry abort |
| `test_coordinator.py` | 3 | Successful fetch, auth → `SETUP_ERROR`, comms → `SETUP_RETRY` |
| `test_fan.py` | 6 | Fan entities created, initial state, inactive areas excluded, turn off, set preset, set percentage |
| `test_init.py` | 2 | Entry loads (`LOADED`), entry unloads cleanly (`NOT_LOADED`) |
| `test_sensor_button_number.py` | 6 | Sensor value, filter reset button press, number value and set |
| `test_switch.py` | 9 | Boost switch on/off, summer mode on, time auto-sync off |

All tests mock `SeviCloudApiClient` — no real network calls are made.

---

## Testing Against the Real API

The unit tests use mocks and never hit the network. A separate set of **live tests** (`tests/test_api_live.py`) call the real SEC Smart API — they are skipped automatically unless you supply an API key.

### 1. Set up your API key

```bash
# Copy the template (once)
cp .env.example .env

# Edit .env and replace the placeholder:
#   SEVI_API_KEY=your-api-key-here
```

`.env` is listed in `.gitignore` — it will never be committed.
The test suite loads `.env` automatically at startup (no external dependency needed).

### 2. Run the live tests

```bash
# Run only live tests
.venv/bin/pytest -m live -v

# Run everything (live tests are skipped without the key)
.venv/bin/pytest
```

You should see output like:

```
tests/test_api_live.py::test_live_authenticate PASSED
tests/test_api_live.py::test_live_get_data PASSED
tests/test_api_live.py::test_live_active_areas PASSED
```

### 3. Inspect raw API responses

```bash
source .env   # loads SEVI_API_KEY into your shell

# List devices
curl -s -H "Authorization: Bearer $SEVI_API_KEY" \
  https://api.sec-smart.app/v1/devices | python3 -m json.tool

# Full device detail (replace <DEVICE_ID>)
curl -s -H "Authorization: Bearer $SEVI_API_KEY" \
  https://api.sec-smart.app/v1/devices/<DEVICE_ID> | python3 -m json.tool
```

### 4. Run the integration inside a development HA instance

```bash
# Symlink the component into your HA config directory
ln -s /path/to/hass-sevi-cloud/custom_components/sevi_cloud \
      /path/to/ha-config/custom_components/sevi_cloud
```

Restart HA, add the integration via **Settings → Devices & Services → Add Integration → SEVI Cloud**, and enter your real API key.

---

## Architecture Overview

```
config_flow.py        — validates the API key once at setup time (GET /devices)
       │
       ▼
__init__.py           — creates SeviCloudApiClient + coordinator, stores in entry.runtime_data
       │
       ├── api.py      — SeviCloudApiClient (async aiohttp, Bearer token auth)
       │
       └── coordinator.py — SeviCloudDataUpdateCoordinator
                              polls async_get_data() every 60 s
                              returns {device_id: full_device_dict}
                              auth errors → ConfigEntryAuthFailed
                              comms errors → UpdateFailed
                                       │
                                       ▼
                             fan.py / switch.py / button.py / sensor.py / number.py
                             Entities iterate coordinator.data at setup;
                             each entity reads its slice of the dict via @property.
```

### Key classes

| Class | File | Purpose |
|---|---|---|
| `SeviCloudApiClient` | `api.py` | Async REST client; raises typed exceptions |
| `SeviCloudDataUpdateCoordinator` | `coordinator.py` | HA coordinator; handles retries and error states |
| `SeviCloudConfigFlow` | `config_flow.py` | UI flow; validates API key via `async_authenticate()` |
| `SeviCloudDeviceEntity` | `entity.py` | Base for device-level entities (sensor, button, number, switches) |
| `SeviCloudAreaEntity` | `entity.py` | Base for area-level entities (fan, boost switch); extends device entity |
| `get_active_areas()` | `data.py` | Returns `[(area_id, label), …]` for areas with hardware installed |

### Exception hierarchy (`api.py`)

```
SeviCloudApiClientError
├── SeviCloudApiClientAuthenticationError   → ConfigEntryAuthFailed (re-prompts user)
└── SeviCloudApiClientCommunicationError    → UpdateFailed / SETUP_RETRY
```

---

## Publishing to HACS

HACS integrations are distributed directly from a GitHub repository — no package registry is involved.

### One-time repository requirements

1. The repository must be **public**.
2. `hacs.json` must exist at the repository root (already present).
3. `custom_components/sevi_cloud/manifest.json` must have a valid `version` field (already present).
4. At least **one GitHub Release** must exist (HACS uses releases to track versions).

### Step-by-step

#### 1. Create a GitHub Release

```bash
# Tag the commit you want to release
git tag v0.1.0
git push origin v0.1.0
```

Then on GitHub go to **Releases → Draft a new release**, select the tag, add release notes, and publish. HACS picks up the tag automatically.

#### 2. Validate the repository (optional but recommended)

Install the [HACS action](https://github.com/hacs/action) — it is already wired up in `.github/workflows/validate.yml`. It runs `hassfest` (HA's own manifest checker) and HACS's own validation on every push to `main` and daily.

Check the Actions tab to confirm both jobs are green before submitting.

#### 3. Submit for the default HACS store (optional)

If you want the integration to appear in the built-in HACS catalogue (so users find it without adding a custom repository):

1. Ensure all [HACS default requirements](https://hacs.xyz/docs/publish/integration) are met (description, README, valid manifest, passing CI).
2. Open a pull request at [hacs/default](https://github.com/hacs/default) and add your repository under `integration/`.

Until your PR is merged, users can still install by adding your repo as a **custom repository** in HACS (see Installation above).

#### 4. Releasing updates

```bash
# Bump the version in manifest.json, then:
git tag v0.2.0
git push origin v0.2.0
# Create a GitHub Release as above
```

HACS users with auto-updates enabled will be notified automatically.

---

## Contributing

1. Fork the repository and create a feature branch off `main`.
2. Run `make check` — all 46 tests must pass and linting must be clean.
3. Open a pull request against `main`. The CI workflows (lint, tests, validate) run automatically.
