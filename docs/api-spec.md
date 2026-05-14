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
