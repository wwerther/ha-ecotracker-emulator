# Verification checklist — sign conventions

> ⚠️ **Do not copy this scenario into production without running through this
> checklist first.** The templates in this folder were derived from a real,
> running SolarEdge SE + EcoFlow Stream Ultra X setup. During the very first
> production days an inverted-sign bug was discovered in the upstream helpers
> that was *masked* by a second inverted reference in the decision template
> -- two wrongs accidentally producing a right output. The files in this
> folder are now spec-conformant, but **you must verify that your own
> SolarEdge installation reports the same sign convention** before relying on
> them.

## Sign convention used here (SunSpec / official wiki)

This scenario follows the convention documented in the upstream
[Template Sensors for Power and Energy](https://github.com/WillCodeForCats/solaredge-modbus-multi/wiki/Template-Sensors-for-Power-and-Energy)
wiki, which matches the SunSpec Modbus standard.

| Sensor                       | Positive means         |
|------------------------------|------------------------|
| `solaredge_m1_ac_power`      | **export** (PV → grid) |
| `solaredge_i1_m1_ac_power`   | **export** (PV → grid) |
| `solaredge_b1_dc_power`      | **charging**           |

Proof from the wiki (single-inverter and inverter+battery topology):

```yaml
- name: "Power - Grid Import"
  state: "{{ min([float(states('sensor.solaredge_m1_ac_power'), 0), 0]) | abs() }}"
- name: "Power - Grid Export"
  state: "{{ max([float(states('sensor.solaredge_m1_ac_power'), 0), 0]) | abs() }}"
```

Live sanity check: while the house is actively **feeding into the grid**,
`sensor.solaredge_i1_m1_ac_power` (and `solaredge_m1_ac_power`) reads
**positive**. Verified on an SE-series setup on 2026-05.

For users whose firmware / CT-clamp orientation reports the inverse
convention, the integration also exposes
`sensor.solaredge_m1_ac_power_inverted` (and
`solaredge_i1_m1_ac_power_inverted`). Either point the helpers at the
`_inverted` sensor, or swap the `min` / `max` operators for
`SE Power Grid Import` and `SE Power Grid Export` in
[`helpers.yaml`](helpers.yaml).

## Reference convention used by this scenario

| Sensor                                     | This scenario expects                     |
| ------------------------------------------ | ----------------------------------------- |
| `sensor.solaredge_m1_ac_power`             | `+` = export (PV → grid), `-` = import    |
| `sensor.solaredge_m1_ac_power_a/_b/_c`     | same as the total, per phase              |
| `sensor.solaredge_b1_dc_power`             | `+` = charging, `-` = discharging         |
| `sensor.solaredge_battery_state_of_charge` | 0..100 %                                  |

EcoTracker JSON output convention (consumed by EcoFlow Stream Ultra X) --
matches [`docs/api-spec.md`](../../docs/api-spec.md):

| Value of `power` in `/v1/json` | Meaning                                            |
| ------------------------------ | -------------------------------------------------- |
| positive                       | grid IMPORT in progress → EcoFlow should discharge |
| negative                       | grid EXPORT in progress → EcoFlow may charge       |
| 0                              | idle                                               |

The four normalisation helpers must always be `>= 0`; the sign of the
underlying meter is encoded in the *name* of the helper, not in its value.

---

## Phase 1 — verify under load (no PV, battery discharging)

Pick a moment with confirmed grid import, e.g. at night with the dishwasher
running. Capture the live values in *Developer Tools → States* or via the
*Template* tab and tick each row:

| Sensor                                                   | Expected                             | Observed | ✓ |
| -------------------------------------------------------- | ------------------------------------ | -------- | - |
| `sensor.solaredge_m1_ac_power`                           | negative (import)                    |          | □ |
| `sensor.se_power_grid_import`                            | positive (= abs of `m1_ac_power`)    |          | □ |
| `sensor.se_power_grid_export`                            | `0`                                  |          | □ |
| `sensor.solaredge_b1_dc_power`                           | negative (discharging)               |          | □ |
| `sensor.se_power_battery_charging`                       | `0`                                  |          | □ |
| `sensor.se_power_battery_discharging`                    | positive (= abs of `b1_dc_power`)    |          | □ |
| Final EcoTracker sensor (e.g. `sensor.ecotracker_power`) | **positive** (spec: import positive) |          | □ |
| EcoFlow Stream Ultra X behaviour in the app              | **discharging into the house**       |          | □ |

## Phase 2 — verify under PV surplus (export, battery may be charging or idle)

Pick a midday moment with confirmed export to the grid (PV running, low
household load, house battery either full or already charging fast):

| Sensor                                      | Expected                             | Observed | ✓ |
| ------------------------------------------- | ------------------------------------ | -------- | - |
| `sensor.solaredge_m1_ac_power`              | positive (export)                    |          | □ |
| `sensor.se_power_grid_import`               | `0`                                  |          | □ |
| `sensor.se_power_grid_export`               | positive (= `m1_ac_power`)           |          | □ |
| Final EcoTracker sensor                     | **negative** (spec: export negative) |          | □ |
| EcoFlow Stream Ultra X behaviour in the app | **charging from the surplus**        |          | □ |

## Phase 3 — per-phase sensors (only if you use the raw passthrough for `powerPhase1..3`)

Same load condition as Phase 2 (known direction). Confirm that the per-phase
Modbus sensors share the same sign convention as the aggregate:

| Sensor                           | Expected during export (Phase 2) | ✓   |
| -------------------------------- | -------------------------------- | --- |
| `sensor.solaredge_m1_ac_power_a` | positive (or 0 if no load on L1) | □   |
| `sensor.solaredge_m1_ac_power_b` | positive (or 0)                  | □   |
| `sensor.solaredge_m1_ac_power_c` | positive (or 0)                  | □   |

If any of them is *negative* while the aggregate is positive → that phase is
backfeeding (e.g. local PV inverter on one phase) and you need a per-phase
sign-normaliser before assigning it to `powerPhase*`.

---

## Other helpers worth re-auditing

If you copied the *broader* SolarEdge helper set that the author maintains in
his own HA (not part of this repo — but shown here so readers can spot the
issues in their own setups), the following are likely affected by any sign
flip:

| Helper                          | Why it might be wrong                                                                                                                                           |
| ------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `SE - Power - Grid - Load`      | chains on `se_power_grid_import` — re-verify after Phase 1                                                                                                      |
| `SE - Power - Grid - Battery`   | chains on `se_power_grid_export`; also watch out for a typo where the formula references `sensor.power_grid_export` (no `se_` prefix → dead sensor)             |
| `SE - Power - Battery - Load`   | chains on `se_power_grid_export`                                                                                                                                |
| `SE - Power - PV - Load`        | chains on `se_power_grid_export`                                                                                                                                |
| `SE - Power - PV - Grid`        | chains on `se_power_consumption` (see next row)                                                                                                                 |
| `SE - Power - Consumption`      | formula `max(i1_ac - m1_ac, 0)` assumes `m1 > 0 = export`; with `m1 > 0 = import` the correct formula is `max(i1_ac + m1, 0)`                                   |
| `SE - Power - Solar Generation` | involves `sensor.solaredge_i1_dc_power` — verify its sign on your inverter (some report DC power flowing **into** the inverter as negative, others as positive) |
| `SE - Power - PV - Battery`     | same `i1_dc_power` dependency as above                                                                                                                          |

These helpers are **not** required by the EcoTracker scenario, but they tend
to appear in companion Energy Dashboards and are silently wrong on any
SolarEdge firmware that reports `m1 > 0 = import`.

---

## Recommended migration order

1. **Now**: migrate only the three EcoTracker-relevant helpers
   (`SE - Power - Grid Import`, `SE - Power - Grid Export`,
   `EcoFlow Virtual Grid Meter`) and run **Phase 1**.
2. **Within the next 24 h**: hit a midday slot and run **Phase 2**.
3. **Once both phases are green**: audit the broader helper set (table above)
   in *Developer Tools → Template*, one helper at a time.
4. **Fix the `sensor.power_grid_export` typo** in
   `SE - Power - Grid - Battery` regardless of sign verdicts — the referenced
   sensor does not exist and currently returns `unknown`.

Tick this file into your scenario folder once all checkboxes are green and
keep it as evidence that the setup has been verified.
