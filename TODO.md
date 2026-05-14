# TODO – EcoTracker Emulator

Living task list. Open items at the top, grouped by priority. Completed items collected at
the bottom under [Done](#-done) for traceability. Keep this file in sync with the actual
implementation state.

Legend: 🔴 blocker · 🟠 functional gap · 🟣 spec compliance · 🟡 code quality ·
🟢 docs / repo hygiene · 🔵 future / nice-to-have

---

## Open

### 🟠 Functional gaps (advertised features missing)

- [ ] **`services.yaml` declares a `reload` service that is not implemented.** Either
  register the service in `async_setup` (using
  `homeassistant.helpers.service.async_register_admin_service` or
  `homeassistant.helpers.reload.async_setup_reload_service`) or remove the YAML entry.
- [ ] **Make mDNS metadata editable post-setup.** `serial`, `product_id` and the `MAC`
  suffix are stored in `entry.data` (set during initial config flow). Allow editing them
  via the options flow once the entity-mapping flow is built; today the user has to
  delete and re-add the integration to change them.

### 🟣 Spec compliance (vs. [`docs/api-spec.md`](docs/api-spec.md))

- [ ] **Energy units are watt-hours, not kWh.** Per spec `energyCounterIn` /
  `energyCounterOut` are in **Wh**. Current `DEFAULT_VALUES` look Wh-shaped (e.g.
  `5502204.6` ≈ 5.5 MWh) but `README.md` / `info.md` document them as kWh. Either:
  - Fix the user-facing docs to say "Wh", **and**
  - Document that mapped HA sensors must be in Wh (or auto-convert from kWh in `api.py`
    based on the source entity's `unit_of_measurement`).
- [ ] **`agePower` is not in the official spec** but **is emitted by real devices** (see
  capture in `docs/api-spec.md`, value e.g. `496`, plausibly age of the last measurement
  in ms). Decision: **keep emulating it.** Open sub-tasks:
  - Document it in `docs/api-spec.md` as an inofficial-but-expected field (done).
  - Make the value dynamic instead of static (e.g. ms since last update of the mapped
    `power` entity, falling back to a fixed value).
- [ ] **Tariff counters missing.** `energyCounterInT1` and `energyCounterInT2`
  (Hoch-/Niedertarif) are part of the spec but not emulated. Per spec they are optional,
  so omitting them by default is fine. Once the options flow exists, expose them as
  optional fields (entity or fallback, plus an "off" choice that omits the key entirely).
- [ ] **Optional fields should be omitable.** Spec says `powerPhaseN` and the tariff
  counters can be absent (single-phase meters, meters without tariff). Today `api.py`
  always emits every key. Add a per-field "not provided / omit" option so strict clients
  see a realistic single-phase response.
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
- [ ] Add a `LICENSE` file (README/info.md claim MIT, but no file present).
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
- [x] 🟢 **Sensor picker filter is now optional + unit-aware.** The picker still
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
