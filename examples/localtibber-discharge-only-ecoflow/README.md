# Localtibber → EcoFlow Stream Ultra X (direct mapping, no templates)

**TL;DR.** If you already run a SolarEdge (or comparable) hybrid inverter
with its own house battery and want to add an EcoFlow Stream Ultra X as a
**second, non-competing discharge source**, you don't need any templates,
helpers or jinja files. **Map the Localtibber sensors directly** in the
EcoTracker Emulator options flow. That's the whole integration.

This folder used to ship clamp-to-non-negative jinja templates. They were
removed on 2026-05-17 after live testing showed they added no value over
direct mapping and actively misbehaved in the common "mixed-sign per-phase"
case (one phase exporting while two import → ghost-export through the
EcoFlow). See [Why no templates](#why-no-templates) below for the full
reasoning.

## When this setup applies

- You have **a Tibber Pulse SML reader** at the grid coupling point, exposed
  through [Localtibber](https://github.com/WaresLO/Localtibber).
- You already have **a hybrid inverter with a house battery** (SolarEdge,
  Fronius, Kostal, Sungrow, Victron …) which acts on PV surplus on its own.
- You want to add **an EcoFlow Stream Ultra X** that only kicks in when the
  hybrid inverter's battery cannot or will not cover house load
  (typically: at night when the house battery is empty, or while it is
  reserved for backup).
- You do **not** want the EcoFlow to charge from the grid or to compete with
  the existing house battery for PV surplus.

If your setup is different (no second battery, or you actively want the
EcoFlow to track PV surplus), see
[`../solaredge-modbus-multi-ecoflow/`](../solaredge-modbus-multi-ecoflow/)
instead.

## Setup

1. **Install Localtibber** and verify the four power sensors update at
   ~1 Hz, with the EcoTracker convention native to SML: positive = grid
   import, negative = grid export.

   Typical entity ids:

   | Field          | Localtibber entity                  | OBIS         |
   |----------------|-------------------------------------|--------------|
   | `power`        | `sensor.localtibber_0100100700ff`   | `1.0.16.7.0` |
   | `powerPhase1`  | `sensor.localtibber_0100240700ff`   | `1.0.36.7.0` |
   | `powerPhase2`  | `sensor.localtibber_0100380700ff`   | `1.0.56.7.0` |
   | `powerPhase3`  | `sensor.localtibber_01004c0700ff`   | `1.0.76.7.0` |
   | `energyCounterIn`  | Localtibber lifetime import (Wh, may need a `* 1000` template if in kWh) | `1.0.1.8.0` |
   | `energyCounterOut` | Localtibber lifetime export (Wh, same caveat) | `1.0.2.8.0` |

2. **Map these directly** in the EcoTracker Emulator integration's options
   flow (one entity per JSON field). No template sensors required.

3. **In the EcoFlow app**, set the Stream Ultra X to **Self-Consumption**
   mode. Other modes (AC-Charging, Time-of-Use, Manual) ignore the meter
   entirely.

That's it. The Stream Ultra X will start regulating against the live grid
reading within a few seconds.

## Why it works without any logic

- **Closed loop is native.** Tibber Pulse sits upstream of *all* household
  inverters and meters the net exchange with the grid. The EcoFlow's own
  AC output therefore shows up immediately in the next Localtibber update
  (~1 s), so the EcoFlow has the correct feedback signal without any
  synthetic subtraction.

- **Charging competition resolves itself by physics, not by logic.** PV
  surplus appears as negative `power` at Localtibber. If the EcoFlow tried
  to charge from it, both inverters would race for the same watts — but the
  hybrid inverter's own battery loop is typically faster (it sees export
  directly on its built-in CT, no network hop), so it wins. In practice
  the EcoFlow's charge command is overridden before it does anything
  meaningful.

- **Discharge only when net-import.** When the hybrid battery is empty and
  the house pulls from the grid, Localtibber shows positive `power` and
  the EcoFlow discharges to cover it. Loop closes, value drops to zero,
  EcoFlow holds the new operating point. Exactly what you want.

## Why no templates

Three reasons emerged from live testing on 2026-05-17:

1. **Clamping ≥ 0 doesn't help if charging is already physically suppressed.**
   The clamp was there to prevent the EcoFlow from charging on PV surplus
   — but as explained above, the hybrid inverter wins that race anyway.
   The clamp adds no protection in practice.

2. **Per-phase clamp creates ghost export.** Real three-phase load profiles
   routinely show mixed signs (e.g. `L1 +120 W, L2 +139 W, L3 −263 W`,
   net `−4 W`). If we clamp the negative phase to 0 and forward the
   positive ones, the EcoFlow receives `+120 / +139 / 0` and discharges
   ~260 W — which is real power injected into the grid, because the
   house was already net-zero. The German utility-metering saldation hides
   the cost, but battery cycles are wasted on export.

3. **The Stream Ultra X has its own dead-band and slew-rate limit.**
   Observed behaviour (see [TODO.md](../../TODO.md) research item for
   details) is consistent with a regulator that ignores small deviations
   around 0 and ramps gradually toward the target. So small absolute
   values of `power` (a few watts) don't trigger spurious charge/discharge
   anyway — there is nothing to suppress at the template layer.

The clean conclusion: forward the meter as-is and let both regulators
do their job. The architecture is correct *because* it is simple.

## Caveats

- **Stale Tibber data → open-loop runaway.** If the Localtibber sensors
  freeze (Pulse loses radio link, integration crashes, USB disconnect), the
  EcoFlow keeps seeing the last value and the loop opens. Empirically the
  Stream Ultra X then ramps to its output limit within seconds, trying to
  drive an error that physically cannot fall. **Watch this in your
  installation.** If it bites, the cleanest fix lives on the emulator
  side: detect `last_updated` age on the mapped entities and omit the
  field (or return `unavailable`) when stale. Tracked in
  [`TODO.md`](../../TODO.md) as a future enhancement.

- **EcoFlow stays idle while the hybrid battery is non-empty.** That is the
  design intent of this scenario, not a bug. If you want the EcoFlow to
  discharge first, change the hybrid inverter's SoC reserve in its own app
  (most have a "minimum SoC" / "backup reserve" slider) rather than trying
  to outsmart it from this side.

- **Energy that would have charged the EcoFlow goes to grid export** once
  the hybrid battery is full. Acceptable trade-off in this scenario; if it
  isn't acceptable for you, run the bidirectional SolarEdge-Modbus scenario
  and accept its complexity.

## Open flank: hybrid-battery → EcoFlow energy shuttling

Even though the EcoFlow rarely *competes* for PV surplus (the hybrid
inverter wins that race), there is a subtler failure mode at night when
both batteries hold charge. Mechanism:

```
Load:        100 W
Hybrid bat.: overshoots its own zero-target → discharges 200 W
             (most regulators don't sit perfectly at 0; small persistent
              bias toward the export side is common)
Tibber sees: 100 − 200 = −100 W   → "export"
EcoFlow reads Tibber → enters charge mode → pulls +100 W from grid
Tibber new:  100 − 200 − (−100) = 0   → equilibrium
```

Net result: the **hybrid battery supplies 200 W**, 100 W reach the load,
**100 W end up in the EcoFlow battery** — with conversion losses on both
sides (~85 % × ~85 % ≈ **27 % round-trip loss**). The hybrid battery
drains roughly twice as fast as the load alone would explain, and the
"saved" energy reappears in the EcoFlow at a discount.

Three conditions must all hold for this to happen:

1. The hybrid inverter persistently overshoots zero by some amount
   (or pulses around it with a downward bias). Many installs are clean
   enough that this is undetectable; some firmwares / CT orientations
   make it visible. Check by watching Localtibber `power` for a few
   minutes with PV idle and no controllable load.
2. The Stream Ultra X accepts AC-charging in Self-Consumption mode (the
   default). See mitigation 1 below.
3. The EcoFlow's own SoC is below 100 %, so it has room to charge.

### Mitigations, cheapest first

1. **EcoFlow app: disable AC-charging if available.** Some Stream Ultra X
   firmwares expose a "Solar only" / "No grid charging" toggle that makes
   the inverter ignore negative `power` values entirely. If this option
   exists on your firmware revision, **this is the clean fix** — single
   source of truth, no template, no physical switch. Whether it exists
   for the Stream Ultra X specifically is open
   ([TODO.md](../../TODO.md) research item).

2. **Hybrid inverter: raise the minimum-SoC reserve** (e.g. 10–20 %).
   Doesn't prevent the phenomenon but caps the worst-case shuttling
   window: once the hybrid battery hits its reserve floor it stops
   discharging, and the system reverts to "Tibber sees real import →
   EcoFlow takes over" — which is exactly the intended scenario.

3. **Physical interrupt on the EcoFlow AC input** (e.g. a Shelly Plug or
   relay on the inverter's grid connection, automated from HA based on
   `localtibber_power < export_threshold`). Heavy-handed but absolutely
   guaranteed: no AC connection, no charge possible. Adds wear on the
   relay if it cycles often, so combine with a generous hysteresis.

4. **Out-of-band visibility on the EcoFlow itself.** Until the Stream
   Ultra X exposes its AC import/export to HA (cloud API, local BLE
   pairing, or a clamp-on energy meter like a Shelly EM/Pro 3EM on the
   inverter's AC lead), you are flying blind: there is no way to tell
   from inside HA whether the inverter is charging from the grid right
   now. Adding such a sensor — even if only for visibility — should
   probably come before any of the active mitigations above.

What we explicitly do **not** recommend: re-introducing a clamp template
on `power` alone. The Stream Ultra X weights per-phase values more heavily
than the aggregate, so the clamp would offer false reassurance while
shuttling continues to leak through the per-phase fields. Per-phase
clamping in turn brings back the ghost-export bug that was the original
reason this folder lost its templates. The current "no templates"
baseline is the honest position; close the open flank above the meter
layer (app setting / SoC reserve / physical relay), not below it.

## What we still don't know about the Stream Ultra X regulator

The behavior described above is reverse-engineered from observation, not
documentation. Open questions, tracked in [`TODO.md`](../../TODO.md):

- Exact dead-band width around 0 (looks like 5–20 W, observed `power = −3 W`
  → no reaction).
- Slew-rate cap when ramping output (looks gradual, no overshoot in our
  test).
- Integration window / hysteresis before reacting to a persistent error.
- Weighting between `power`, `powerAvg` and `powerPhase1..3` when they
  conflict.
- Behavior when optional fields (`powerPhase*`, `energyCounter*T1/T2`) are
  omitted entirely.
- Role of `agePower` (if any) in staleness detection.

If you have data points from your own installation, **pull requests with
new findings — or with a different scenario folder showing a setup we
haven't covered — are very welcome.** Especially valuable: controlled
step-input experiments with `curl`/cron and an EcoFlow output log, so we
can pin down the dead-band and slew-rate numbers.
