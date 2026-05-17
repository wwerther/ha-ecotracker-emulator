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
  installation. Adjust them to your hardware sizing. The same file also
  exposes anti-oscillation / liveness tunables that default to neutral:
  - `DEADZONE_OUTPUT` (W, default `0`): value returned in the dead zone.
    Set to a small positive number (e.g. `10`) to bias the system into a
    minimal grid draw and avoid being misread as "meter offline" by
    EcoFlow firmwares that distrust an exact, persistent `0`.
  - `DEADZONE_JITTER` (W, default `0`): optional symmetric noise added to
    `DEADZONE_OUTPUT` on every re-render. `3..5` keeps the value visibly
    moving so the inverter cannot interpret it as a frozen sensor. Note
    that this only ticks while *some* upstream sensor still ticks -- the
    cleaner liveness primitive is a dynamic `agePower`.
  - `EXPORT_DAMPING` / `IMPORT_DAMPING` (default `1.0`): factor `<= 1.0`
    applied to the charge / discharge signal. Values like `0.9` tell
    EcoFlow to undershoot the measured surplus/load so a tiny residual
    stays on the grid side, preventing limit-cycling around `0`.
  - `EXPORT_OVERSHOOT` (W, default `0`): the opposite of `EXPORT_DAMPING` --
    a positive value makes EcoFlow charge *more* than the measured export
    in order to clear surplus spikes faster, at the cost of brief grid
    import. Do not combine with `EXPORT_DAMPING < 1.0`.

## Tested with

| Component | Version |
|-----------|---------|
| Home Assistant Core | 2026.5.1 |
| EcoTracker emulator | 0.1.0 |
| EcoFlow Stream Ultra X firmware | V1.0.2.1 |
| SolarEdge Modbus Multi | latest as of 2026-05 |

## Lessons learned (2026-05) — read this before tuning anything

The original version of this scenario assumed that the EcoFlow Stream Ultra X
would politely follow the aggregate `power` value coming from `/v1/json`,
just like the EcoTracker spec implies. **It does not.** Two days of live
debugging surfaced a handful of properties of the Stream Ultra X firmware
that the manufacturer documents nowhere and that completely change how the
emulator must be wired into a SolarEdge installation. Capturing them here so
nobody else has to re-derive them from scratch.

### 1. Per-phase values dominate over the aggregate

When all four power keys (`power`, `powerAvg`, `powerPhase1..3`) are present,
the inverter regulates **primarily on the per-phase values**. Two observed
events:

- Aggregate `power = -1 W`, phases summing to `-474 W` (export-dominated) →
  Stream Ultra X **charged with ~600 W**, in line with the per-phase export
  but far above what the aggregate would justify.
- Aggregate `power = -11 W`, `powerAvg = +89 W`, phase sum `+88 W` →
  Stream Ultra X **discharged with ~800 W**, again driven by the per-phase
  picture, not by the much smaller `power` value.

Practical consequence: **you cannot keep the inverter calm by tuning only
the aggregate**. Either omit `powerPhase1..3` (let the firmware fall back to
the aggregate) or steer every phase deliberately.

### 2. Per-phase sensors must use EcoTracker convention, not SunSpec

`sensor.solaredge_m1_ac_power_a/_b/_c` from `solaredge-modbus-multi` follow
the **SunSpec** convention: `positive = export`. The EcoTracker JSON spec
uses the **inverse** convention for `powerPhase*`: `positive = import,
negative = feed-in`. Wiring raw SunSpec phase sensors straight into the
options flow (as the older revisions of this README recommended!) sign-flips
the per-phase information and causes the inverter to interpret a healthy
export as a heavy import — full discharge. Use one of:

- `sensor.localtibber_010024/38/4c0700ff` (SML / Tibber Pulse already uses
  the EcoTracker convention) — the cleanest source if you have a Tibber
  Pulse, *and* it also solves the closed-loop problem from §3 below.
- Inverted SolarEdge helpers (`* -1` template per phase).
- Omit `powerPhase1..3` entirely and rely on `power` only (matches §1).

### 3. The biggest one: closed-loop vs. open-loop meter placement

The Stream Ultra X behaves as a **negative-feedback regulator** that
expects the reported meter to be the **net grid-coupling-point reading**,
i.e. the meter value *after* the EcoFlow's own contribution has been
subtracted. That is exactly where a physical EcoTracker would be installed.

If the sensor you feed into `power` does **not** see the EcoFlow's own
output (typical for an inverter-side SolarEdge meter that sits upstream of
the EcoFlow's injection point, or for any meter installed on the PV side
only), the regulator loop is broken:

```
EcoFlow injects 400 W   →   "meter" still shows +400 W import (unchanged)
        ↑                            ↓
"there is still import" ←   "I need to inject more"
```

The inverter ramps to maximum until it hits a current/thermal limit. That
is the symptom "EcoFlow runs to max charge/discharge for no apparent
reason". Two ways to close the loop:

- **Physical (recommended):** make sure the sensor you map to `power`
  actually measures the grid coupling point. Tibber Pulse on the utility
  SML meter does this natively; that is why mapping `localtibber_…`
  immediately stabilises the system in our tests.
- **Synthetic (works with any upstream meter):** subtract the EcoFlow's
  reported output power from the meter reading and feed the difference
  as `power`:

  ```text
  virtual_meter = solaredge_meter − ecoflow_output_w
  ```

  This requires a HA sensor that reports the EcoFlow's instantaneous AC
  output (e.g. from `hassio-ecoflow-cloud` or the official EcoFlow
  integration). Mind the **latency** of the upstream source — cloud
  integrations with > 10 s update intervals produce a sluggish loop that
  overshoots and oscillates. A local MQTT/BLE source is strongly
  preferred.

This is also a strong hint that the emulator itself should grow a
"self-output compensation" option (track this in [`TODO.md`](../../TODO.md)
under Future enhancements).

### 4. Stale data triggers fallback modes, not graceful degradation

Several non-obvious states put the Stream Ultra X into a default
charge/discharge mode that **ignores the meter completely** until the
condition clears:

- `energyCounterIn = energyCounterOut = 0` for an extended period — looks
  like an uninitialised meter to the firmware; the inverter falls back to
  internal defaults (observed at ~580 W charge / ~800 W discharge).
- Persistent zero/jittering-around-zero `power` with no movement on the
  energy counters — same fallback.
- A configuration mismatch in the EcoFlow app (operating mode set to
  "AC Charging", "Time-of-Use", or "Manual" instead of
  "Self-Consumption") — the meter is ignored on purpose.
- Stream Ultra X SoC below its low-cut-off — the firmware refuses to
  discharge regardless of meter readings.

If you see the inverter sitting at a suspiciously round wattage that does
not react to changes in `/v1/json`, **check the app first**, before touching
the template.

### 5. What "self-stabilising" actually looks like

Once meter placement is correct (§3), the inverter follows the meter
linearly. Concretely, ramping `power` from `+200 W` to `+400 W` in
discrete 50 W steps should produce a matching ramp in EcoFlow output power
within one or two polling cycles, with a small residual import of a few
watts at steady state (the EcoFlow under-shoots slightly to avoid
overshooting into export). If you see anything else — step changes from 0
to max, or constant output regardless of meter value — you are still in
fallback mode (§4) or open-loop (§3).

### 6. What we still do not know

- **Exact weighting** between `power`, `powerAvg` and per-phase values in
  the Stream Ultra X firmware. We have qualitative evidence that phases
  dominate but no documented decision rule.
- **`agePower` semantics.** The real device emits values around `496 ms`
  in the captured trace, consistent with "age of the last measurement in
  milliseconds". Whether (and how aggressively) the Stream Ultra X uses
  this field for liveness detection is unknown; experiments needed.
- **Behaviour with omitted fields.** The spec marks `powerPhase*` and
  `energyCounterInT*` as optional. Whether the Stream Ultra X tolerates a
  JSON response without these keys, or whether absence triggers a
  fallback, has not been verified.

These open questions are tracked in [`../../TODO.md`](../../TODO.md) under
*EcoFlow Stream Ultra X behaviour — research*.
