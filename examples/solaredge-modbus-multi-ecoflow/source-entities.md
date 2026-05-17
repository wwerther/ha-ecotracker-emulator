# Source entities

Sensors that feed this scenario. Install the listed integrations first, then
build the derived helpers in [`helpers.yaml`](helpers.yaml).

## SolarEdge Modbus Multi (HACS)

Install <https://github.com/WillCodeForCats/solaredge-modbus-multi> against
your inverter via Modbus TCP. Sign conventions (SunSpec / official wiki,
also verified against a live SE-series setup as of 2026-05):

| Entity                                         | Sign convention                              |
|------------------------------------------------|----------------------------------------------|
| `sensor.solaredge_m1_ac_power`                 | `+` = export to grid, `-` = import from grid |
| `sensor.solaredge_m1_ac_power_a / _b / _c`     | per-phase, same convention as the total      |
| `sensor.solaredge_m1_ac_power_inverted`        | inverse helper exposed by the integration: `+` = import, `-` = export |
| `sensor.solaredge_i1_m1_ac_power`              | inverter-attached meter reading (same convention as `m1`) |
| `sensor.solaredge_b1_dc_power`                 | `+` = charging, `-` = discharging            |
| `sensor.solaredge_battery_state_of_charge` (%) | 0..100                                       |
| `sensor.solaredge_i1_ac_power`                 | inverter AC output power                     |
| `sensor.solaredge_b1_status`                   | `B_STATUS_CHARGE / DISCHARGE / IDLE / ...`   |

> ⚠️ **Verify before relying on this table.** Some SolarEdge firmware
> revisions and CT-clamp orientations invert the m1 sign. Run Phase 1 /
> Phase 2 in [`VERIFICATION.md`](VERIFICATION.md) on your own installation
> before EcoFlow starts regulating. If your meter is inverted, either swap
> `min` / `max` in [`helpers.yaml`](helpers.yaml) or point the helpers at
> `sensor.solaredge_m1_ac_power_inverted` instead.

## Localtibber (optional cross-check)

Tibber Pulse readings of the SML meter, useful as a sanity check against the
Modbus values.

| Entity                              | Meaning            |
|-------------------------------------|--------------------|
| `sensor.localtibber_0100100700ff`   | Total active power (W) |
| `sensor.localtibber_0100240700ff`   | Active power L1 (W)    |
| `sensor.localtibber_0100380700ff`   | Active power L2 (W)    |
| `sensor.localtibber_01004c0700ff`   | Active power L3 (W)    |

## Derived helpers

The decision logic in [`ecotracker-power.jinja`](ecotracker-power.jinja) does
**not** read the raw Modbus sensors directly. It consumes a small set of
strictly non-negative, well-named helpers (`se_power_grid_import`,
`se_power_grid_export`, `se_power_battery_charging`,
`se_power_battery_discharging`). Their definitions live in
[`helpers.yaml`](helpers.yaml).
