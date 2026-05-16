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
- [ ] `manifest.json` placeholders:
  ~~`codeowners: ["@dein_github_name"]`~~ ✅ set to `@wwerther`,
  ~~documentation / issue_tracker URLs~~ ✅ set to
  `https://github.com/wwerther/ha-ecotracker-emulator`. (Entry kept open until repo
  actually exists publicly under that URL.)
- [x] No `iot_class` review – changed `local_push` → `local_polling` (clients poll
  `/v1/json`; the integration never pushes). ✅ fixed 2026-05-14

### 🟢 Documentation & repo hygiene

- [x] `info.md` describes `agePower` as "Lebensenergie (Wattsekunden)" – per real-device
  capture this is the **age of the last power reading in milliseconds**. Fix the
  description. ✅ fixed 2026-05-14
- [x] Add a `LICENSE` file (README/info.md claim MIT, but no file present). ✅ added 2026-05-14
- [x] Add a `.gitignore` (Python/`__pycache__`, `.venv`, `.DS_Store`, etc.) – ✅ already in repo (verified 2026-05-14)
- [x] `hacs.json` could declare `homeassistant` (minimum HA version) and
  `zip_release: false` for clarity. ✅ added 2026-05-14 (`homeassistant: 2024.11.0`)

### 🔵 Future enhancements (parking lot)

- [ ] **Per-client profiles ("virtual meter instances").** Serve different payloads on
  the same `/v1/json` endpoint depending on the requesting client's IP, so several
  systems (e.g. two EcoFlow inverters that should each see a different subset of
  loads, or a tariff-aware view for a smart-meter dashboard) can pair with the same
  emulated EcoTracker.

  Constraint that drives everything below: HA can't expose `/v1/json` twice on the
  same port and mDNS broadcasts are network-wide, so we always have **exactly one
  config entry, one mDNS announcement, one HTTP view**. Per-client differentiation
  happens purely at HTTP-response time based on `request.remote`.

  #### Preferred implementation — **Option B: YAML free-text field in the options flow**

  Cheapest path to a working feature, HACS-friendly, no second source of truth.

  - **Options flow.** Add **one** new field to the existing single-step options
    form, `extra_profiles`, rendered as a multiline `TextSelector`. The user
    pastes a YAML list:

    ```yaml
    - name: Wechselrichter Garten
      ip_match: 192.168.1.42         # single IP or CIDR (e.g. 192.168.1.0/24)
      sensors:
        power: sensor.gartenseite_power
        powerPhase1: sensor.garten_l1
      fallbacks:
        powerPhase2: 0
      omit:
        - powerPhase3
    - name: Tarif-Dashboard
      ip_match: 10.0.0.0/24
      sensors:
        energyCounterIn: sensor.tarif_bezug
    ```

    No `ALL` / catch-all entry needed in the YAML — the existing flat options
    (configured through the normal options form) **are** the implicit default
    profile and handle every request that no explicit profile matches.

    Validate on submit with a `voluptuous` schema + `ipaddress.ip_network(
    strict=False)` for each `ip_match`. On parse error keep the user's text and
    surface `errors={"extra_profiles": "invalid_profile_yaml"}` with the line/key
    that failed in `description_placeholders`.

  - **Default profile stays implicit.** The existing flat
    `<key>_entity` / `<key>_fallback` / `<key>_omit` options *are* the catch-all
    profile. No migration needed, no schema break, existing installs keep working
    untouched. New `extra_profiles` simply prepend in front of that default; no
    `ip_match: ALL` keyword in the YAML — if a request matches nothing, it falls
    through to the default by construction.

  - **API view.** On each request:
    1. resolve `request.remote` (honour `X-Forwarded-For` only when HA's
       `http.use_x_forwarded_for` is enabled — read from `hass.config`),
    2. iterate `extra_profiles` top-to-bottom, first match wins,
    3. on no match fall through to the existing flat-options code path (= default
       profile).

    Build the JSON from the matched profile's `sensors` (entity lookup → state →
    unit conversion as today), filling missing keys from `fallbacks`, dropping
    keys listed in `omit`. Keys not mentioned anywhere inherit from the default
    profile so users only have to specify *differences*.

  - **Tasks.**
    - [ ] `const.py`: `CONF_EXTRA_PROFILES = "extra_profiles"`.
    - [ ] `config_flow.py`: add multiline TextSelector + YAML/schema validation
          helper; round-trip the raw text so the user sees what they typed.
    - [ ] `api.py`: profile-matching helper (`_select_profile(remote_ip, profiles)`),
          plug into existing response builder; keep current code path as the
          fallback branch.
    - [ ] README / README.de: a short "Advanced: per-client profiles" section
          with the YAML example above and the X-Forwarded-For caveat.
    - [ ] Translations: `extra_profiles` label + help text + the
          `invalid_profile_yaml` error message in `en.json` / `de.json`.
    - [ ] Diagnostics (when that lands): include parsed profile list and which
          profile a given test IP would resolve to; redact entity IDs only if HA
          policy requires.

  - **Caveats to document.**
    - Reverse-proxy / Nginx in front of HA hides the real client IP unless
      `X-Forwarded-For` is configured **both** in HA *and* the proxy.
    - IPv6 clients work as long as the `ip_match` is written in IPv6 notation
      (e.g. `fe80::/10`); mixed-family matches silently miss.
    - mDNS still announces a single `ecotracker-<MAC>` device — all clients
      pair with the same identity, differentiation is HTTP-only.

  #### Option C — full multi-step UI (only if there is ever spare time)

  If demand for a click-through editor arises, build a proper multi-step
  `async_step_init` menu with *Add / Edit / Delete / Reorder / Done*, real
  `EntitySelector`s per field, and `entry.options["profiles"]` as a structured
  list of dicts (with stable UUIDs to survive reorders). Migration from Option B
  is trivial: parse the YAML free-text once on upgrade, write it into the
  structured list, drop the YAML field. Cost is mostly UI plumbing; until then
  the YAML field covers 100 % of the functional ground.

  #### Rejected — `configuration.yaml`

  Two sources of truth, conflicts with the config-flow entry, and HACS reviewers
  discourage new YAML config for config-flow integrations. Not pursued.
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

_Last reviewed: 2026-05-16._
