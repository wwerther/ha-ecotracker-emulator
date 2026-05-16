# Source entities

Sensors that feed this scenario. Install the listed integrations first, then
build the derived helpers in [`helpers.yaml`](helpers.yaml).

## SolarEdge Modbus Multi (HACS)

Install <https://github.com/WillCodeForCats/solaredge-modbus-multi> against
your inverter via Modbus TCP. Sign conventions (verified against a
live SE-series setup as of 2026-05):

| Entity                                         | Sign convention                              |
|------------------------------------------------|----------------------------------------------|
| `sensor.solaredge_m1_ac_power`                 | `+` = import from grid, `-` = export to grid |
| `sensor.solaredge_m1_ac_power_a / _b / _c`     | per-phase, same convention as the total      |
| `sensor.solaredge_b1_dc_power`                 | `+` = charging, `-` = discharging            |
| `sensor.solaredge_battery_state_of_charge` (%) | 0..100                                       |
| `sensor.solaredge_i1_ac_power`                 | inverter AC output power                     |
| `sensor.solaredge_b1_status`                   | `B_STATUS_CHARGE / DISCHARGE / IDLE / ...`   |

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
