# Source entities

Sensors that feed this scenario. Install the listed integrations first, then
build the derived helpers in [`helpers.yaml`](helpers.yaml).

## SolarEdge Modbus Multi (HACS)

| Entity | Meaning |
|--------|---------|
| `sensor.solaredge_m1_ac_power`   | Grid meter total AC power (signed: + import, - export) |
| `sensor.solaredge_m1_ac_power_a` | Grid meter L1 AC power |
| `sensor.solaredge_m1_ac_power_b` | Grid meter L2 AC power |
| `sensor.solaredge_m1_ac_power_c` | Grid meter L3 AC power |
| `sensor.solaredge_b1_state_of_energy` | House battery state of energy (Wh) |
| `sensor.solaredge_b1_status`     | House battery status (`B_STATUS_CHARGE`, `B_STATUS_DISCHARGE`, `B_STATUS_IDLE`, ...) |
| `sensor.solaredge_b1_dc_power`   | House battery DC power (signed: + charge, - discharge) |
| `sensor.solaredge_i1_ac_power`   | Inverter AC power |
| `sensor.solaredge_i1_m1_ac_power_inverted` | Inverter AC power with sign flipped to match meter convention |
| `sensor.solaredge_battery_state_of_charge` | House battery SoC (%) |

## Localtibber (optional cross-check)

Tibber Pulse readings of the SML meter, useful as a sanity check against the
Modbus values.

| Entity | Meaning |
|--------|---------|
| `sensor.localtibber_0100100700ff` | Total active power (W) |
| `sensor.localtibber_0100240700ff` | Active power L1 (W) |
| `sensor.localtibber_0100380700ff` | Active power L2 (W) |
| `sensor.localtibber_01004c0700ff` | Active power L3 (W) |

## Derived helpers

The decision logic in [`ecotracker-power.jinja`](ecotracker-power.jinja) does
**not** read the raw Modbus sensors directly. It consumes a small set of
strictly non-negative, well-named helpers (`se_power_grid_import`,
`se_power_grid_export`, `se_power_battery_charging`,
`se_power_battery_discharging`). Their definitions live in
[`helpers.yaml`](helpers.yaml).
