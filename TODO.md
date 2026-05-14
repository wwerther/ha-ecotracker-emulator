# TODO – EcoTracker Emulator

Living task list. Open items at the top, grouped by priority. Completed items collected at
the bottom under [Done](#-done) for traceability. Keep this file in sync with the actual
implementation state.

Legend: 🔴 blocker · 🟠 functional gap · 🟣 spec compliance · 🟡 code quality ·
🟢 docs / repo hygiene · 🔵 future / nice-to-have

---

## Open

### 🟠 Functional gaps (advertised features missing)

_(none currently open)_

### 🟣 Spec compliance (vs. [`docs/api-spec.md`](docs/api-spec.md))

- [ ] **`agePower` is not in the official spec** but **is emitted by real devices** (see
  capture in `docs/api-spec.md`, value e.g. `496`, plausibly age of the last measurement
  in ms). Decision: **keep emulating it.** Open sub-tasks:
  - Document it in `docs/api-spec.md` as an inofficial-but-expected field (done).
  - Make the value dynamic instead of static (e.g. ms since last update of the mapped
    `power` entity, falling back to a fixed value).
- [ ] **Tariff counters missing.** `energyCounterInT1` and `energyCounterInT2`
  (Hoch-/Niedertarif) are part of the spec but not emulated. Per spec they are optional,
  so omitting them by default is fine. Once added, they should hook into the same
  per-field omit toggle that already exists for the other fields.
- [ ] **Discovery / fingerprint fidelity.** Real device returns a custom HTML 404 on every
  unknown path (`/`, `/favicon.ico`, ...) pointing at `/v1/json` and the everHome docs
  (see `docs/api-spec.md` → "Real-device capture"). Currently HA serves its own 404 for
  those paths. Optionally add a catch-all view that mimics the original HTML body byte
  for byte to improve fingerprint match for strict clients.
- [ ] **JSON formatting.** Real device returns tab-indented, line-broken JSON with a
  specific `Content-Length` (188 in the sample). `self.json(...)` in HA produces
  minified JSON. If clients fingerprint on body shape, switch to a manual
  `web.Response(text=json.dumps(data, indent='\t'), content_type='application/json')`.

### 🟡 Code quality & robustness

- [ ] `EcotrackerJsonView` is registered as a class. HA accepts that, but storing per-entry
  state on a singleton view is fragile – consider passing the `hass`/entry through and
  registering an instance.
- [ ] Logging coverage is minimal. `_LOGGER` exists in `__init__.py` and logs register /
  unregister, but `api.py` and `config_flow.py` are silent. Add at least a `warning` when
  a configured entity state is invalid / unavailable.
- [ ] Type hints are incomplete (`api.py`, `config_flow.py`, helper functions in
  `__init__.py`). AGENTS.md states type hints are mandatory.
- [ ] German comments in code (e.g. `__init__.py`, `config_flow.py`). Per AGENTS.md the
  code base should be English; translate remaining comments.
- [ ] `manifest.json` placeholders: `codeowners: ["@dein_github_name"]`, documentation /
  issue_tracker URLs still contain `dein_name`. Replace with real values before release.
- [ ] No `iot_class` review – `local_push` is questionable for a passive HTTP responder;
  `local_polling` may be more accurate.

### 🟢 Documentation & repo hygiene

- [ ] `info.md` describes `agePower` as "Lebensenergie (Wattsekunden)" – per real-device
  capture this is the **age of the last power reading in milliseconds**. Fix the
  description.
- [x] Add a `LICENSE` file (README/info.md claim MIT, but no file present). ✅ added 2026-05-14
- [ ] Add a `.gitignore` (Python/`__pycache__`, `.venv`, `.DS_Store`, etc.) – currently
  none in the repo.
- [ ] `hacs.json` could declare `homeassistant` (minimum HA version) and
  `zip_release: false` for clarity.

### 🔵 Future enhancements (parking lot)

- [ ] Reverse proxy / port-80 add-on guidance (some clients hard-code port 80).
- [ ] Diagnostics support (`async_get_config_entry_diagnostics`) for easier debugging.
- [ ] Unit tests with `pytest-homeassistant-custom-component`.
- [ ] GitHub Actions: hassfest + HACS validation workflow.
- [ ] Allow a manual "refresh values now" service.

---

## ✅ Done

Resolved items, newest first. Keep the resolution note so we remember _why_ something was
changed.

### 2026-05-14
- [x] 🟠 **mDNS metadata editable post-setup (reconfigure flow).** The integration card
  now exposes a *Reconfigure* entry (`async_step_reconfigure` in `config_flow.py`).
  MAC suffix, serial, product ID and port can be changed in place, the form is pre-
  filled with the current values, the entry title is updated to `ecotracker-<MAC>`,
  and the entry is reloaded so the mDNS service is re-published with the new identity.
  Sensor mappings stay untouched (those are still handled via the regular options flow).
- [x] 🟣 **Optional fields can be omitted from the JSON.** Each field gained an *Omit*
  checkbox in the options flow. When set and no usable sensor value is available, the
  key is dropped from `/v1/json` entirely instead of falling back to the static number.
  This covers the spec note that `powerPhaseN` (and later the tariff counters) may be
  absent on single-phase / single-tariff meters. The default is *off*, so existing
  setups keep emitting every key.
- [x] 🟣 **Auto-convert source units to spec units in `api.py`.** Mapped sensors are now
  read with their `unit_of_measurement` and rescaled: power fields are normalised to
  **W** (`mW`/`kW`/`MW` supported), energy counters to **Wh** (`kWh`/`MWh` supported).
  Sensors without a unit – or with an unknown one – are passed through unchanged and
  logged at debug level so the JSON output stays usable while mismatches remain
  diagnosable. The README/docs already advertise Wh, so behaviour now matches.- [x] � **Removed phantom `reload` service.** `services.yaml` declared
  `ecotracker_emulator.reload` but never registered it via
  `hass.services.async_register`, so calling it would have failed. The integration
  card's built-in *Reload* button covers manual reloads, and the existing options-flow
  update listener already triggers `async_reload` after every options change. The file
  was deleted.
- [x] �🟢 **Sensor picker filter is now optional + unit-aware.** The picker still
  prefers sensors with the matching `device_class`, but additionally accepts any
  sensor whose `unit_of_measurement` fits (W/kW/mW for power, Wh/kWh/MWh for energy)
  so hand-rolled template sensors without a `device_class` show up. A new toggle
  *Show all sensors* in the options flow disables filtering entirely as an escape
  hatch. The currently-selected entity always stays visible even if it would be
  filtered out.
- [x] 🟢 **Sensor picker filtered by device_class.** The options-flow entity selectors
  now restrict the dropdown to sensors with the matching `device_class` (`power` for
  `power`/`powerAvg`/`powerPhaseN`, `energy` for `energyCounterIn/Out`). `agePower`
  stays unfiltered (no native device_class equivalent).
- [x] 🟢 **Bilingual README.** HACS does not natively support multi-language READMEs (it
  only renders one file). Added an English `README.md` (the file HACS shows) plus a
  German `README.de.md`, with a language switcher at the top of each. Aligns with
  AGENTS.md ("documentation in English"); the German version is kept for the primary
  audience.- [x] � **README/info.md explain the actual purpose** (EcoFlow inverters require an
  EcoTracker via local API + mDNS discovery, IP no longer manually configurable in the
  EcoFlow app). Updated installation steps to match the new MAC-suffix / serial /
  product-id flow, added link to `docs/api-spec.md`, dropped dead `DEVELOPMENT.md`
  reference in favour of `AGENTS.md`.
- [x] �🟠 **Options flow now maps every JSON field to a sensor / fallback.**
  `EcotrackerOptionsFlow` was just a stub. It now renders a form with one row per key in
  `DEFAULT_VALUES`: an `EntitySelector(domain="sensor")` (optional, can be cleared) plus
  a `NumberSelector` fallback. Results are written to `entry.options` under the
  `<key>_entity` / `<key>_fallback` keys that `api.py` already consumes; cleared entity
  selections are normalised to `None`. Translation strings for the `options.init` step
  added in `en.json` and `de.json`. Also dropped the now-unnecessary
  `OptionsFlow.__init__(config_entry)` (deprecated by HA in favour of the inherited
  `self.config_entry`).- [x] � **mDNS metadata configurable.** `serial`, `product_id` and the MAC suffix were
  hard-coded in `__init__.py`. The unused `MDNS_SERVICE_NAME` constant in `const.py` was
  also a leftover.
  - Config flow now asks for `mac_suffix` (12 hex chars, defaults to a random suffix
    using the EcoTracker OUI `B43A45`), `serial` (12 hex chars, random default) and
    `product_id` (default `1137`). Service name is computed as
    `ecotracker-<MAC_SUFFIX>` and exposed via mDNS; serial / productid go into the
    TXT records. Validation + i18n error strings added; `MDNS_SERVICE_NAME` removed in
    favour of `SERVICE_NAME_PREFIX` + `MAC_OUI` + `CONF_*` keys. Legacy entries with
    `service_name` in `entry.data` are still served via a fallback in
    `_resolve_service_name()`.
- [x] 🔴 **Domain mismatch.** Folder is `custom_components/ecotracker_emulator/`, but
  `manifest.json` and `const.py` declared `domain = "ecotracker"`. HA requires these to be
  identical, otherwise the integration fails to load.
  - `DOMAIN` and `manifest.domain` now both read `ecotracker_emulator`; HTTP view name
    updated to `ecotracker_emulator:json`.
  - Note: `entry.data["service_name"]` (default `ecotracker-B43A452249C9`) is the **mDNS
    advertised name** and intentionally keeps the hyphenated form – it is not a HA domain.
- [x] 🔴 **mDNS service is never deregistered.** `_publish_mdns_service()` registered the
  `ServiceInfo`, but `async_unload_entry` did not call `aiozc.async_unregister_service(...)`.
  - `__init__.py` now stores `aiozc` and `ServiceInfo` in
    `hass.data[DOMAIN][entry.entry_id]` and unregisters them on unload (with logging on
    register/failure).
- [x] 🔴 **`hass.config.api.local_ip` is unreliable / may be `None`** (e.g. when HA listens
  on `0.0.0.0`).
  - `__init__.py` now uses `network.async_get_source_ip(hass, MDNS_TARGET_IP)` and raises
    a clear `RuntimeError` when no routable IP is found. Added `network` to manifest
    `dependencies`. Confirmed via `avahi-browse` that the correct LAN IP is advertised.
- [x] 🔴 **`requirements` pinned `zeroconf==0.132.2`.** Custom integrations must not pin
  `zeroconf`; HA ships its own version.
  - `requirements` is now `[]`, dependencies extended to `["http", "network", "zeroconf"]`.
- [x] 🟠 **Multiple instances unsupported.** `EcotrackerJsonView._get_entry()` always
  returned the first config entry; nothing prevented a second entry from being created
  even though `/v1/json` and the port are global.
  - `async_step_user` aborts with `single_instance_allowed` when an entry already exists;
    `unique_id` set to `DOMAIN`. Translation strings added in `en.json` and `de.json`.
- [x] 🟢 **Translations:** `translations/en.json` contained German strings ("einrichten",
  "Dienstname").
  - Real English `en.json` provided; existing `de.json` kept; both include the
    `single_instance_allowed` abort key.

---

_Last reviewed: 2026-05-14._
