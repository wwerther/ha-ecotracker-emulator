# EcoTracker Emulator for Home Assistant

<p align="center">
  <img src="assets/logo.png" alt="EcoTracker Emulator logo" width="180">
</p>

> 🌐 **Language / Sprache:** **English** · [Deutsch](README.de.md)

Emulates an [everHome EcoTracker](https://everhome.cloud/en/developer/ecotracker)
energy monitor: publishes the matching mDNS service (`_everhome._tcp`) and serves the
expected JSON payload on `/v1/json` with energy data.

## Why?

Recent **EcoFlow inverters** (PowerStream and similar) only accept **EcoTracker devices
via their local API** as an external power meter — no detour through a linked cloud
account is possible anymore. On top of that, the EcoFlow app **no longer lets you enter
the meter's IP address manually**; pairing is done **exclusively via mDNS discovery** on
the local network.

Anyone who already measures consumption / feed-in inside Home Assistant (Shelly 3EM,
Tibber Pulse, smart meter integrations, etc.) is stuck: without a real EcoTracker device,
the EcoFlow inverter receives no readings. This integration closes that gap:

- It **impersonates an EcoTracker** towards the EcoFlow app (mDNS service, JSON API,
  TXT records, service name `ecotracker-<MAC>` using the EcoTracker OUI `B4:3A:45`).
- The **values come from arbitrary Home Assistant sensors**, mapped per JSON field via
  the options flow — with a numeric fallback for the case a sensor is not yet reporting
  a valid value.
- The EcoFlow inverter can therefore use the consumption / feed-in measured in HA as its
  control input **without buying additional hardware** or linking a cloud account.

## Installation

1. Add this repository as an HACS custom repository (category: Integration).
2. Install the "EcoTracker Emulator" integration via HACS.
3. Restart Home Assistant.
4. Go to Settings → Devices & Services → Add Integration → "EcoTracker Emulator".
5. Confirm or adjust the MAC suffix, serial and product ID (sensible defaults are
   pre-filled — the MAC suffix intentionally starts with the EcoTracker OUI `B43A45`).
6. Open the integration's **Options** afterwards and assign a sensor or a fixed fallback
   value to each JSON field.

## How it works

- The integration publishes an mDNS service (`_everhome._tcp`) under the configured name
  (`ecotracker-<MAC>`), including the `serial`, `productid` and `ip` TXT records.
- `http://<HA-IP>:8123/v1/json` returns the EcoTracker-compatible JSON payload (fields:
  `power`, `powerAvg`, `agePower`, `powerPhase1..3`, `energyCounterIn`,
  `energyCounterOut`).
- Energy counters are expected in **watt-hours (Wh)** to match the official spec — see
  [`docs/api-spec.md`](docs/api-spec.md).

## Tested with

The integration is actively in use against the following combination. Reports about
other setups are welcome — please open an issue with your versions.

| Component | Version |
|-----------|---------|
| Home Assistant Core | **2026.5.1** |
| EcoTracker emulation profile | **EcoTracker IR** (mDNS service `_everhome._tcp`, JSON `/v1/json`) |
| EcoFlow inverter | **Stream Ultra X** |
| EcoFlow inverter firmware | **V1.0.2.1** |

## Known limitations

- The HTTP API runs on the **Home Assistant port (default 8123)**, not on port 80.
  Current EcoFlow clients accept that because the port is announced via the mDNS TXT
  record — clients hard-coded to port 80 need a reverse proxy.
- Only **one instance** can be configured per Home Assistant (the `/v1/json` path is
  global).
- Authentication is disabled (just like on the real device) — the endpoint is freely
  readable on the local network.
- The **EcoFlow app shows the EcoTracker IR as „offline / disconnected“** unless the
  paired inverter is **actively using** the meter as its power-source input. As soon as
  the inverter polls and uses the values, the meter’s telemetry tile in the app starts
  showing live values; if the inverter stops using it, the tile flips back to
  „disconnected“. Pairing itself works either way and `/v1/json` keeps responding
  normally. The Tibber Pulse, for comparison, always shows up as connected because the
  EcoFlow app talks to it via the Tibber cloud rather than the local API — a path the
  emulator cannot replicate. So the indicator is **really an „in active use“ flag**, not
  a true reachability check. No fix known; reports of app versions where this differs
  are welcome via issue.

## Supported platforms

- Home Assistant OS
- Home Assistant Container
- Home Assistant Supervised / Core (anywhere `zeroconf` and HA's HTTP server run)

## Development

See [`AGENTS.md`](AGENTS.md) for setup, syncing to HAOS and coding conventions,
[`docs/api-spec.md`](docs/api-spec.md) for the emulated spec including a real-device
capture, and [`TODO.md`](TODO.md) for the current work-in-progress.

## License

MIT
