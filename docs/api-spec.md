# EcoTracker `/v1/json` – Official API specification

> **Language note:** Field descriptions below are quoted **verbatim** from the
> manufacturer's documentation and therefore in German. Do not paraphrase – this file is
> the reference our emulator is benchmarked against.

## Endpoint

```
GET /v1/json
```

## Example response

```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "power": 125,
  "powerAvg": 100,
  "powerPhase1": 50,
  "powerPhase2": 50,
  "powerPhase3": 25,
  "energyCounterIn": 145000,
  "energyCounterInT1": 100000,
  "energyCounterInT2": 45000,
  "energyCounterOut": 4500
}
```

## Field reference (verbatim)

- **`power`** – beinhaltet die aktuelle Leistung in Watt. Der Wert ist negativ bei
  Einspeisung und positiv bei Bezug.
- **`powerAvg`** – beinhaltet den durchschnittlichen `power` Wert in Watt der letzten
  Minute.
- **`powerPhase1`** – beinhaltet die aktuelle Leistung in Watt auf Phase 1. Der Wert ist
  negativ bei Einspeisung und positiv bei Bezug. Wird nicht von jedem Stromzähler
  bereitgestellt.
- **`powerPhase2`** – beinhaltet die aktuelle Leistung in Watt auf Phase 2. Der Wert ist
  negativ bei Einspeisung und positiv bei Bezug. Wird nicht von jedem Stromzähler
  bereitgestellt.
- **`powerPhase3`** – beinhaltet die aktuelle Leistung in Watt auf Phase 3. Der Wert ist
  negativ bei Einspeisung und positiv bei Bezug. Wird nicht von jedem Stromzähler
  bereitgestellt.
- **`energyCounterIn`** – beinhaltet den Zählerstand des Bezugs in Wattstunden.
- **`energyCounterInT1`** – beinhaltet den Hochtarif-Zählerstand des Bezugs. Dieser Wert
  ist nicht immer vorhanden und kann auch ohne Hoch- und Niedertarif vorhanden sein.
- **`energyCounterInT2`** – beinhaltet den Niedertarif-Zählerstand des Bezugs. Dieser Wert
  ist nicht immer vorhanden und kann auch ohne Hoch- und Niedertarif vorhanden sein.
- **`energyCounterOut`** – beinhaltet den Zählerstand der Einspeisung in Wattstunden.

## Real-device capture

Captured 2026-05-14 from a physical EcoTracker at `10.16.20.39` (firmware unknown).
Useful as a ground-truth reference – behaviour observed here trumps assumptions.

### `GET /` (and any unknown path, e.g. `/favicon.ico`) → `404` with HTML hint

```http
HTTP/1.1 404 Not Found
Content-Type: text/html
Content-Length: 349

everHome Local API: <a href='/v1/json'>/v1/json</a><br>everHome Local API Documentation: <a href='https://everhome.cloud/en/developer/ecotracker'>Local-API Documentation</a><br>everHome Homepage: <a href='https://everhome.cloud'>everHome.cloud</a><br>everHome Cloud-APi: <a href='https://everhome.cloud/en/developer/api'>Cloud-API Documentation</a>
```

> Note the typo `Cloud-APi` – kept verbatim for fingerprinting.

### `GET /v1/json` → `200`

```http
HTTP/1.1 200 OK
Content-Type: application/json
Content-Length: 188

{
	"power":	-3127,
	"powerAvg":	-3114,
	"agePower":	496,
	"powerPhase1":	-1025,
	"powerPhase2":	-1176,
	"powerPhase3":	-925,
	"energyCounterOut":	5552927.8,
	"energyCounterIn":	1541618.4
}
```

### Observations from the capture

- **Pretty-printed body, indented with TABs.** Keys and values are separated by `\t` and
  each key/value pair sits on its own line. `Content-Length` (188) matches that formatting
  exactly – minified JSON would be shorter.
- **No authentication, no `Server` / `Date` / `Connection` headers** beyond the two shown.
- **`agePower` IS emitted by the real device**, even though it is not part of the
  manufacturer's published spec. Value here is `496` – plausible as **age of the last
  measurement in milliseconds** (sub-second). Treat it as an inofficial-but-expected
  field and keep emulating it.
- **`energyCounterOut` ≈ 5.55 GWh and `energyCounterIn` ≈ 1.54 GWh** is implausible →
  confirms the unit is **Wh** (≈ 5.55 MWh / 1.54 MWh). Matches the manufacturer's spec.
- **No tariff fields** (`energyCounterInT*`) on this device – consistent with spec stating
  they are optional.
- **Three-phase meter:** all three `powerPhase*` keys present, all negative, summing to
  `-3126 W` ≈ `power` (`-3127 W`). Consistent with the sign convention "negative =
  feeding in".
- **404 page is HTML, not JSON**, and serves as a discovery hint pointing clients to
  `/v1/json`. Worth replicating in the emulator for full fingerprint compatibility.

## Notes for the emulator

The following items are differences between the spec above and the current emulator
implementation. Track / resolve them via [`../TODO.md`](../TODO.md):

- **Units.** `energyCounterIn` / `energyCounterOut` are documented in **watt-hours (Wh)**,
  not kWh. The emulator's defaults and any user-mapped sensor values must follow the same
  unit – if a HA sensor reports kWh, multiply by 1000 before serving (or document this
  expectation clearly).
- **`agePower`.** Currently shipped in `DEFAULT_VALUES`/`api.py` but **not part of the
  official spec**. Decide whether to keep it (some clients may expect it from older
  firmware) or drop it.
- **Tariff fields.** `energyCounterInT1` / `energyCounterInT2` are spec'd but **not yet
  emulated**. They are explicitly described as optional, so the emulator may continue to
  omit them – but should expose them via the options flow once entity mapping is built.
- **Optional vs. always-present.** Per spec, the `powerPhaseN` and `energyCounterInT*`
  fields may be absent. The emulator currently always returns all keys. If strict
  compatibility with single-phase meters becomes important, consider letting the user
  mark a field as "not provided" so it is omitted from the JSON response entirely.
