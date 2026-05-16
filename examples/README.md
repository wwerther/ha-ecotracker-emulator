# Example setups

Worked examples that show how to feed the EcoTracker emulator with realistic
power and energy values from existing Home Assistant integrations.

Each subfolder is a self-contained scenario with:

- `README.md` -- hardware setup, goal, decision strategy, step-by-step install
- `source-entities.md` -- which integration entities the scenario consumes
- `helpers.yaml` -- ready-to-paste template helpers
- `ecotracker-<field>.jinja` -- the final template per EcoTracker JSON field
  (`power`, `powerPhase1`, ...)

## Available scenarios

| Folder | Source | Target device |
|--------|--------|---------------|
| [solaredge-modbus-multi-ecoflow](solaredge-modbus-multi-ecoflow/) | SolarEdge SE inverter + house battery via Modbus | EcoFlow Stream Ultra X |

## Contributing a scenario

If you wire the emulator to a different upstream (KNX, Shelly, smart meter,
custom MQTT, ...) please open a pull request adding a new folder following the
same layout. Keep templates English-commented; explanations and decision
narratives may use any language but English is preferred.
