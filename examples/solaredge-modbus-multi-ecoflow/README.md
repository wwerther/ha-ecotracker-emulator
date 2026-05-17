# SolarEdge Modbus Multi + EcoFlow Stream Ultra X

End-to-end example that turns a SolarEdge inverter + house battery setup into a
power signal for an **EcoFlow Stream Ultra X** paired with this emulator.

> ⚠️ **Before adopting this scenario, work through
> [`VERIFICATION.md`](VERIFICATION.md).** The sign conventions assumed here
> follow the SunSpec / official upstream wiki convention
> (`solaredge_m1_ac_power > 0 = export`, `solaredge_b1_dc_power > 0 = charging`)
> and were confirmed on the author's installation. Some SolarEdge firmwares
> / CT-clamp orientations invert the m1 sign; in that case point the helpers
> at `sensor.solaredge_m1_ac_power_inverted` (also exposed by the
> integration) or flip the `min` / `max` operators in `helpers.yaml`. The
> checklist walks you through verifying the helpers under load and under PV
> surplus before EcoFlow starts regulating against them.

## Setup

- **PV / inverter:** SolarEdge SE series, read via the
  [SolarEdge Modbus Multi](https://github.com/WillCodeForCats/solaredge-modbus-multi)
  HACS integration (Modbus TCP).
- **House battery:** SolarEdge BAT-10K (or similar), exposed via the same
  Modbus integration as `solaredge_b1_*`.
- **Additional storage:** EcoFlow Stream Ultra X, paired in the EcoFlow app
  with the emulator advertised by this custom component (`_everhome._tcp`).
- **Optional sanity check:** Tibber Pulse via the
  [Localtibber](https://github.com/WaresLO/Localtibber) integration to verify
  the Modbus meter against the physical SML reading.

## What we want to achieve

The EcoFlow Stream Ultra X should behave as a *secondary* battery that
complements the existing SolarEdge house battery instead of fighting it:

1. **Real PV surplus** -> EcoFlow charges with the full export power.
2. **House battery is actively charging** -> EcoFlow stays out of the way; it
   only charges if there is genuine grid export on top of the house-battery
   draw.
3. **Load on the house side** (grid import or house-battery discharging):
   - house battery still has capacity -> EcoFlow covers ~50 % of the load,
   - house battery essentially empty (SoC <= 5 %) -> EcoFlow covers 100 %.
4. **Everything else** -> EcoFlow stays idle.

## Inputs

See [`source-entities.md`](source-entities.md) for the integration entities
this scenario consumes. None of them are read by the decision template
directly; instead they feed a small set of normalised helpers (next step).

## Step-by-step installation

1. **Install the source integrations** (SolarEdge Modbus Multi, optionally
   Localtibber) until the entities listed in
   [`source-entities.md`](source-entities.md) are populated.
2. **Add the four normalisation helpers** from [`helpers.yaml`](helpers.yaml).
   Either drop the file into a `template_helpers/` folder and include it from
   `configuration.yaml`:
   ```yaml
   # configuration.yaml
   template: !include_dir_merge_list template_helpers/
   ```
   or recreate each helper via *Settings → Devices & Services → Helpers →
   "Template a sensor"* using the same name (the entity_id must end up as
   `sensor.se_power_grid_import`, `..._grid_export`,
   `..._battery_charging`, `..._battery_discharging`).
   Restart Home Assistant once.
3. **Create the final EcoTracker Power sensor** from
   [`ecotracker-power.jinja`](ecotracker-power.jinja). Two equivalent ways:
   - **UI helper (recommended for one-off scenarios):** *Settings → Devices
     & Services → Helpers → "Template a sensor"*. Name it `EcoTracker Power`,
     set `unit_of_measurement: W`, `device_class: power`,
     `state_class: measurement`, and paste the **entire body** of
     `ecotracker-power.jinja` into the *State template* field.
   - **YAML (recommended if you keep helpers under version control):** add a
     `template:` block in `configuration.yaml`:
     ```yaml
     template:
       - sensor:
           - name: EcoTracker Power
             unique_id: ecotracker_power
             unit_of_measurement: W
             device_class: power
             state_class: measurement
             state: |
               # ... paste the contents of ecotracker-power.jinja here ...
     ```
     (`!include` does **not** work inside `template:` blocks — the value of
     `state` has to be inline.)
4. **Verify** that `sensor.ecotracker_power` shows sensible values: positive
   on PV surplus, negative when EcoFlow should discharge, `0` in the dead
   zone. Use *Developer Tools → States* to check.
5. **Configure the EcoTracker emulator** (*Settings → Devices & Services →
   EcoTracker Emulator → Configure*):
   - `power` → `sensor.ecotracker_power`
   - `powerPhase1..3` → see the **Per-phase values** section below
   - `agePower` → omit, or back with a number-template that tracks the
     last-changed timestamp of `sensor.ecotracker_power` (advanced, not
     required for EcoFlow to function)
   - `energyCounterIn` / `energyCounterOut` → either omit, or point at
     SolarEdge / Tibber lifetime counters (Wh)
6. **Pair the EcoFlow Stream Ultra X** in the EcoFlow app. It will discover
   the emulator via mDNS and start polling `/v1/json`.

## Per-phase values (`powerPhase1..3`)

The EcoTracker emulator exposes `powerPhase1..3` so phase-aware inverters can
balance load per phase. You have three options, in order of increasing
effort:

1. **Raw passthrough (recommended for SolarEdge SE).** Wire the
   per-phase Modbus sensors straight through in the options flow:
   - `powerPhase1` → `sensor.solaredge_m1_ac_power_a`
   - `powerPhase2` → `sensor.solaredge_m1_ac_power_b`
   - `powerPhase3` → `sensor.solaredge_m1_ac_power_c`

   Note that the per-phase sum will **not** equal `sensor.ecotracker_power`
   (which carries the EcoFlow-targeted decision logic), but the Stream Ultra X
   tolerates the discrepancy. EcoFlow uses the per-phase values for phase
   balancing and the aggregate `power` for state-of-charge decisions.
2. **Omit `powerPhase1..3` entirely.** Toggle the `_omit` switch for each
   phase field in the emulator options. The inverter will spread load across
   phases without external guidance. Works, but you lose phase balancing.
3. **Per-phase decision logic.** Replicate the same logic as
   `ecotracker-power.jinja` for each phase. Only worthwhile if you have
   genuine per-phase load steering and per-phase house-battery accounting,
   which the standard SolarEdge setup does not.

## Caveats

- **Sign convention -- verify on your installation.** This example assumes
  the SunSpec / official-wiki convention
  `sensor.solaredge_m1_ac_power > 0 = export` / `< 0 = import` and
  `sensor.solaredge_b1_dc_power > 0 = charging` / `< 0 = discharging`, which
  matches an SE-series inverter as of 2026-05.
  **Before you trust the helpers, check it on your own system**: pick a
  moment with known direction (e.g. midday with PV surplus -> export is
  positive, at night under load -> import is positive on the
  `se_power_grid_import` helper) and confirm the raw Modbus sensor sign
  matches what the table in [`source-entities.md`](source-entities.md)
  claims. If yours is inverted, either swap the `min` / `max` operators in
  `helpers.yaml` or point the helpers at
  `sensor.solaredge_m1_ac_power_inverted`.
- **EcoTracker JSON sign convention** (consumed by EcoFlow): positive
  `power` value = grid import / inverter should discharge, negative value =
  grid export / inverter may charge. The EcoFlow Stream Ultra X uses the
  meter as a virtual grid sensor it regulates against -- it is not
  controlled directly but reacts to the simulated grid state.
- **Update interval.** The SolarEdge Modbus integration polls at a
  configurable rate (default 30 s). EcoFlow polls `/v1/json` roughly every
  second, so the emulator will reply with the most recently cached value --
  there is no benefit to polling faster than the source sensors update.
- **Modbus reconnect.** While the Modbus integration is reconnecting, the
  source sensors go `unavailable`. With the `has_value(...)` availability
  guards in `helpers.yaml` the normalisation helpers also go `unavailable`,
  so `sensor.ecotracker_power` cleanly stays `unavailable` instead of
  pretending the house just stopped consuming power. The EcoTracker
  emulator omits unavailable fields from its JSON response by default.
- **Tunables.** The thresholds in
  [`ecotracker-power.jinja`](ecotracker-power.jinja) (`CHARGE_THRESHOLD`,
  `EXPORT_THRESHOLD`, `SPLIT_RATIO`, `SOC_EMPTY`, ...) reflect the author's
  installation. Adjust them to your hardware sizing.

## Tested with

| Component | Version |
|-----------|---------|
| Home Assistant Core | 2026.5.1 |
| EcoTracker emulator | 0.1.0 |
| EcoFlow Stream Ultra X firmware | V1.0.2.1 |
| SolarEdge Modbus Multi | latest as of 2026-05 |
