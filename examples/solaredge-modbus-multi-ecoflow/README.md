# SolarEdge Modbus Multi + EcoFlow Stream Ultra X

End-to-end example that turns a SolarEdge inverter + house battery setup into a
power signal for an **EcoFlow Stream Ultra X** paired with this emulator.

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
2. **Add the template helpers** from [`helpers.yaml`](helpers.yaml) to your
   Home Assistant configuration:
   ```yaml
   # configuration.yaml
   template: !include_dir_merge_list template_helpers/
   ```
   then drop `helpers.yaml` and `ecotracker-power.jinja` into
   `template_helpers/`. Restart Home Assistant.
3. **Verify** that `sensor.ecotracker_power` shows sensible values (positive
   on export, negative on import, 0 in the dead zone).
4. **Open the EcoTracker emulator options** in Home Assistant (Settings ->
   Devices & Services -> EcoTracker Emulator -> Configure) and pick
   `sensor.ecotracker_power` as the entity for the `power` field. Leave
   `powerPhase1..3`, `agePower`, `energyCounter*` either omitted or backed by
   their own sensors / fallbacks depending on what your inverter requires.
5. **Pair the EcoFlow Stream Ultra X** in the EcoFlow app. It will discover
   the emulator via mDNS and start polling `/v1/json`.

## Caveats

- **Sign convention.** EcoFlow Stream Ultra X expects *positive* = household
  exports / inverter may charge, *negative* = household imports / inverter
  should discharge. The template enforces this; do not feed it a sensor that
  uses the inverse convention.
- **Update interval.** The SolarEdge Modbus integration polls at a configurable
  rate (default 30 s). EcoFlow polls `/v1/json` roughly every second, so the
  emulator will reply with the most recently cached value -- there is no
  benefit to polling faster than the source sensors update.
- **Modbus reconnect.** While the Modbus integration is reconnecting, the
  source sensors go `unavailable` and the template falls back to `0`. EcoFlow
  will idle until values resume, which is the safe behaviour.
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
