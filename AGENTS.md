# AGENTS.md – EcoTracker Emulator for Home Assistant

This file provides context, conventions, and workflows for AI agents or developers working on this integration. This is your source of truth. Keep it up to date as the project evolves. Add sections as needed (e.g., architecture overview, coding standards, testing procedures). Document relevant decisions in this file.
Please also keep README.md and info.md in sync with any user-facing changes. Please also add and maintain a TODO.md file for tracking work in progress and future enhancements.
All documentation should be written in English language. Anyway communication to the developer should be in his prefered language (German in this case).
Please translate to English where needed and still German code is insight. Exception to that rule is of course the translations directory, where all user-facing strings must be in the appropriate language (en.json, de.json, etc.) and never hardcoded in the code.

## Project Overview

**Goal:** Emulate an EcoTracker energy monitor device on the network so that other devices (e.g., inverters, apps) can discover it via mDNS and request energy data via HTTP.

**How it works:**
- Publishes an mDNS service `_everhome._tcp` with a configurable name (e.g., `ecotracker-B43A452249C9`).
- Provides an HTTP endpoint `/v1/json` that returns a JSON payload with energy values.
- Values can be mapped to real Home Assistant sensor entities or static fallback values.

## Repository Structure

```
ha_ecotracker_emulator/             # Repository root
├── custom_components/
│   └── ecotracker_emulator/        # Integration directory – MUST match `domain` in manifest.json
│       ├── __init__.py             # Setup/unload, mDNS publishing
│       ├── manifest.json           # Metadata, dependencies
│       ├── config_flow.py          # Setup UI and options flow
│       ├── api.py                  # HTTP view for /v1/json
│       ├── const.py                # Constants (DOMAIN, defaults, etc.)
│       ├── services.yaml           # Optional – custom services
│       └── translations/           # Localization (en.json, de.json, …)
├── README.md                       # User-facing documentation
├── info.md                         # HACS detail page (only used if hacs.json `render_readme` is false)
├── hacs.json                       # HACS metadata
├── sync_to_ha.sh                   # rsync script for deployment
├── TODO.md                         # Active work items / known issues
└── .gitignore
```

> ⚠️ **Domain rule:** The folder under `custom_components/` must be identical to the `domain` value
> in `manifest.json` and to `DOMAIN` in `const.py`. Currently the folder is
> `ecotracker_emulator`, so `DOMAIN` must be `"ecotracker_emulator"` (see TODO.md).

## Technology Stack

- **Language:** Python 3.12+
- **Framework:** Home Assistant Integration (custom_component)
- **Networking:** `zeroconf` (python package) for mDNS
- **HTTP:** `aiohttp` (via Home Assistant's `HomeAssistantView`)
- **SSH Sync:** `rsync` over SSH (port 22222 for HAOS host access)

## Key Files & Responsibilities

| File | Responsibility |
|------|----------------|
| `const.py` | Central constants: DOMAIN, API path, mDNS service type, default values. |
| `manifest.json` | Domain name, version, dependencies (`zeroconf`, `http`), config_flow flag. |
| `config_flow.py` | User setup (service name, port) and options flow for entity mapping. |
| `api.py` | `EcotrackerJsonView` class – serves `/v1/json`, reads entities/fallbacks from config entry options. |
| `__init__.py` | `async_setup_entry`: registers API view, starts mDNS service; `async_unload_entry`: cleanup. |
| `sync_to_ha.sh` | Local script to rsync code to HAOS (root@homeassistant.lan:22222). |

## Development Workflow (Local VS Code → HAOS)

1. **Edit code** locally in VS Code (no SSH remote needed – use local folder).
2. **Run sync script** from repo root:
   ```bash
   ./sync_to_ha.sh
   ```
   This uses `rsync` to copy `custom_components/ecotracker_emulator/` to the path configured
   in `sync_to_ha.sh` (`HA_TARGET_DIR`, default `/root/homeassistant/custom_components/ecotracker_emulator`).
   The default `SSH_PORT` is `22` (HA Add-on SSH); use `22222` for direct HAOS host access.
3. **Reload integration** in Home Assistant (faster than full restart):
   - Developer Tools → "Integrationen neu laden" (reload integrations)
   - Or click the integration card → gear icon → "Neu laden"
4. **Check logs** in HAOS:
   - Developer Tools → Logs
   - Or via SSH: `docker logs homeassistant -f` (HAOS specific)

## Testing the Emulator

### Verify mDNS advertisement
On any machine in the same network:
```bash
avahi-browse -r _everhome._tcp
```
Should show your configured service name (e.g., `ecotracker-B43A452249C9`).

### Test HTTP endpoint
```bash
curl http://<HA_IP>:8123/v1/json
```
Expected response (example):
```json
{
  "power": 13,
  "powerAvg": 2,
  "agePower": 2635906,
  "powerPhase1": 83,
  "powerPhase2": -168,
  "powerPhase3": 98,
  "energyCounterOut": 5502204.6,
  "energyCounterIn": 1540610.7
}
```

## Coding Conventions

- Follow [Home Assistant Development Guidelines](https://developers.home-assistant.io/docs/development_guidelines/).
- Use `async` functions wherever possible (Home Assistant is async-first).
- Type hints are mandatory.
- Constants go into `const.py`; avoid magic strings.
- All user-facing strings must be in `translations/en.json` (or other language files) – never hardcoded.
- Configuration entries use `entry.data` for initial setup (immutable) and `entry.options` for user-changed settings (mutable via options flow).
- Use `hass.data[DOMAIN][entry.entry_id]` to store runtime data (e.g., the Zeroconf `ServiceInfo` object for cleanup).

## Configuration Flow & Options

### Step 1: User Setup (`config_flow.py`)
- User provides **service_name** (mDNS name) and **port** (usually 8123).
- Creates config entry with `data` (service_name, port) and initial `options` (entity_id placeholders + fallback values from `DEFAULT_VALUES`).

### Step 2: Options Flow (planned)
- Allows user to map each JSON field to a sensor entity or set a fixed fallback number.
- Stored in `entry.options` under keys like `power_entity`, `power_fallback`, etc.
- Implement `EcotrackerOptionsFlow` (already stubbed in `config_flow.py`).

## Important Constraints

- **Port 80 vs 8123:** The real EcoTracker usually uses port 80. Home Assistant runs on 8123 by default. If the client hardcodes port 80, you must set up a reverse proxy (e.g., Nginx) on the HAOS host. The mDNS announcement can advertise port 80, but the actual endpoint is still on 8123 – this causes a mismatch. **Recommendation:** Keep port 8123 and document this limitation.
- **Authentication:** The real device has no auth. Therefore `requires_auth = False` in `api.py`. This makes the endpoint publicly accessible on your local network – acceptable for an emulator, but warn users.
- **Zeroconf cleanup:** Always deregister the service in `async_unload_entry` to avoid stale announcements. Store the `ServiceInfo` object in `hass.data`.

## Known Pitfalls

- **Permission denied** when syncing via non-root user → always use `root@homeassistant.lan:22222`.
- **Integration not loading** after sync → reload integrations via Developer Tools, not just restart HA.
- **mDNS not visible** → check that `zeroconf` dependency is installed and network allows multicast.
- **Options flow not saving** → ensure `async_get_options_flow` is properly registered in `config_flow.py`.

## Adding New Features

### Adding a new JSON field
1. Add the field key and a default fallback to `DEFAULT_VALUES` in `const.py`.
2. Update `api.py` to include the new key in the loop (or add manually if custom logic needed).
3. Extend the options flow (when implemented) to allow entity/fallback configuration for the new field.

### Changing mDNS properties
Modify `__init__.py` → `_publish_mdns_service()`, specifically the `properties` dict. Currently includes `ip`, `serial`, `productid`. Make them configurable via options flow if needed.

## Useful Commands (local terminal)

> Replace `<PORT>` with `22` (Add-on SSH) or `22222` (HAOS host SSH) depending on your setup.

```bash
# Sync code to HAOS
./sync_to_ha.sh

# Follow HA logs (via SSH)
ssh -p <PORT> root@homeassistant.lan "docker logs homeassistant -f"

# Test mDNS manually from HAOS
ssh -p <PORT> root@homeassistant.lan "avahi-browse -r _everhome._tcp"

# Restart HA Core remotely
ssh -p <PORT> root@homeassistant.lan "ha core restart"
```

## Future Enhancements (Ideas)

- Full options flow for entity mapping (UI with selectors).
- Allow configuring mDNS service name, serial, productid via options.
- Support for multiple emulated instances (different service names).
- Add a service to manually trigger update of the JSON response.
- Port forwarding or reverse proxy add-on to support port 80.

## References

- [Home Assistant Custom Component Docs](https://developers.home-assistant.io/docs/creating_component_index/)
- [Zeroconf in HA](https://developers.home-assistant.io/docs/creating_component_code/#zeroconf)
- [HTTP Views](https://developers.home-assistant.io/docs/dev_101_http/)
- [Config Entries & Options Flow](https://developers.home-assistant.io/docs/config_entries_config_flow_handler/)

---

**When working on this code, always keep the emulation goal in mind:** Act exactly like a real EcoTracker would, but let the user control the data sources. Avoid adding features that would break compatibility with existing clients (e.g., unexpected headers, authentication, or path changes).
```