# TODO – EcoTracker Emulator

Status: **First draft, not yet executed/tested in Home Assistant.**
Order is roughly _blocking → important → nice-to-have_. Tick items off and keep this file in
sync with the actual implementation state.

---

## 🔴 Blocking bugs (integration will not load / not work as advertised)

- [x] **Domain mismatch.** Folder is `custom_components/ecotracker_emulator/`, but
  `manifest.json` and `const.py` declared `domain = "ecotracker"`. Home Assistant requires
  these to be identical, otherwise the integration fails to load.
  - Resolved 2026-05-14: `DOMAIN` and `manifest.domain` now both read
    `ecotracker_emulator`; HTTP view name updated to `ecotracker_emulator:json`.
  - Note: `entry.data["service_name"]` (default `ecotracker-B43A452249C9`) is the **mDNS
    advertised name** and intentionally keeps the hyphenated form – it is not a HA domain.
- [ ] **mDNS service is never deregistered.** `_publish_mdns_service()` registers the
  `ServiceInfo`, but the comment _“ServiceInfo speichern, um später zu deregistrieren”_ is
  not implemented. `async_unload_entry` returns `True` without calling
  `aiozc.async_unregister_service(...)`. → Stale announcements after reload/unload.
  - Store the `ServiceInfo` (and the `aiozc` reference) in
    `hass.data[DOMAIN][entry.entry_id]` and unregister on unload.
- [ ] **`hass.config.api.local_ip` is unreliable / may be `None`** (e.g. when HA listens on
  `0.0.0.0`). Use `homeassistant.components.network.async_get_source_ip(hass, MDNS_TARGET_IP)`
  or `homeassistant.helpers.network.get_url(...)` to obtain a routable LAN IP, and guard
  against `None` before calling `socket.inet_aton`.
- [ ] **`requirements` pins `zeroconf==0.132.2`.** Custom integrations must not pin
  `zeroconf`; HA ships its own version and pinning will either be ignored or break the
  install. Remove from `requirements`; `dependencies: ["zeroconf", "http"]` is enough.

## 🟠 Functional gaps (advertised features missing)

- [ ] **Options flow is only a stub.** `EcotrackerOptionsFlow.async_step_init` shows an
  empty form; there is no UI to map JSON fields to entities or edit fallbacks, even though
  README/info.md promise it.
  - Build a schema that, for every key in `DEFAULT_VALUES`, offers
    `selector.EntitySelector(domain="sensor")` (optional) **and** a numeric fallback.
  - Persist results into `entry.options` using the `<key>_entity` / `<key>_fallback`
    naming already expected by `api.py`.
- [ ] **`services.yaml` declares a `reload` service that is not implemented.** Either
  register the service in `async_setup` (using
  `homeassistant.helpers.service.async_register_admin_service` or
  `homeassistant.helpers.reload.async_setup_reload_service`) or remove the YAML entry.
- [ ] **mDNS metadata is hard-coded** (`serial = "a5e235f42c75"`, `productid = "1137"`).
  Make these configurable via the options flow as documented in AGENTS.md.
- [ ] **`MDNS_SERVICE_NAME` constant in `const.py` is unused** – the value comes from
  `entry.data["service_name"]` instead. Remove it or actually use it as the default.
- [ ] **Multiple instances unsupported.** `EcotrackerJsonView._get_entry()` always returns
  the first config entry. Either restrict to a single entry
  (`async_step_user` → `self._async_current_entries()`-check) or carry the entry id in the
  URL / register one view per entry.

## 🟡 Code quality & robustness

- [ ] `EcotrackerJsonView` is registered as a class. HA accepts that, but storing per-entry
  state on a singleton view is fragile – consider passing the `hass`/entry through and
  registering an instance.
- [ ] No logging anywhere (`_LOGGER = logging.getLogger(__name__)` missing). Add at least
  `info` on register/unregister and `warning` when a configured entity state is invalid.
- [ ] Type hints are incomplete (`api.py`, `config_flow.py`, helper functions in
  `__init__.py`). AGENTS.md states type hints are mandatory.
- [ ] German comments in code (e.g. `__init__.py`, `config_flow.py`). Per AGENTS.md the
  code base should be English; translate remaining comments.
- [ ] `manifest.json` placeholders: `codeowners: ["@dein_github_name"]`, documentation /
  issue_tracker URLs still contain `dein_name`. Replace with real values before release.
- [ ] No `iot_class` review – `local_push` is questionable for a passive HTTP responder;
  `local_polling` may be more accurate.

## 🟢 Documentation & repo hygiene

- [ ] **Translations:** `translations/en.json` contains German strings ("einrichten",
  "Dienstname"). Provide a real English `en.json` and add `de.json` for German.
- [ ] **Translation keys for the options flow** are missing entirely (will be needed once
  the options flow is implemented).
- [ ] `README.md` references a non-existent `DEVELOPMENT.md`. Either create it or link
  `AGENTS.md` instead.
- [ ] `info.md` describes `agePower` as "Lebensenergie (Wattsekunden)" – on real EcoTracker
  devices this is the **age of the last power reading in milliseconds**. Verify and fix.
- [ ] Add a `LICENSE` file (README/info.md claim MIT, but no file present).
- [ ] Add a `.gitignore` (Python/`__pycache__`, `.venv`, `.DS_Store`, etc.) – currently
  none in the repo.
- [ ] `hacs.json` could declare `homeassistant` (minimum HA version) and
  `zip_release: false` for clarity.

## 🔵 Future enhancements (parking lot)

- [ ] Reverse proxy / port-80 add-on guidance (some clients hard-code port 80).
- [ ] Diagnostics support (`async_get_config_entry_diagnostics`) for easier debugging.
- [ ] Unit tests with `pytest-homeassistant-custom-component`.
- [ ] GitHub Actions: hassfest + HACS validation workflow.
- [ ] Allow a manual “refresh values now” service.

---

_Last reviewed: 2026-05-14 – initial walkthrough of the first draft._
