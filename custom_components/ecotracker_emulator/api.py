"""HTTP view that serves the EcoTracker-compatible /v1/json payload."""
from __future__ import annotations

import logging

from homeassistant.components.http import HomeAssistantView
from homeassistant.core import HomeAssistant

from .const import API_PATH, DEFAULT_VALUES, DOMAIN

_LOGGER = logging.getLogger(__name__)

# Fields that are expected in watts / watt-hours according to the EcoTracker
# spec. Sensors mapped here may report in a different unit (especially kWh for
# energy meters in Home Assistant) – we normalise on the fly so the JSON output
# always matches the spec the EcoFlow inverters expect.
_POWER_FIELDS: frozenset[str] = frozenset(
    {"power", "powerAvg", "powerPhase1", "powerPhase2", "powerPhase3"}
)
_ENERGY_FIELDS: frozenset[str] = frozenset(
    {"energyCounterIn", "energyCounterOut"}
)

# Multipliers to bring a sensor reading to the spec unit. Keys are
# unit_of_measurement strings as Home Assistant exposes them.
_POWER_TO_W: dict[str, float] = {
    "W": 1.0,
    "kW": 1_000.0,
    "MW": 1_000_000.0,
    "mW": 0.001,
}
_ENERGY_TO_WH: dict[str, float] = {
    "Wh": 1.0,
    "kWh": 1_000.0,
    "MWh": 1_000_000.0,
}


def _convert(key: str, value: float, unit: str | None) -> float:
    """Convert ``value`` to the spec unit (W for power, Wh for energy).

    Unknown / missing units are passed through unchanged with a debug log; this
    keeps sensors with non-standard units usable while making mismatches
    diagnosable from the log.
    """
    if key in _POWER_FIELDS:
        table = _POWER_TO_W
    elif key in _ENERGY_FIELDS:
        table = _ENERGY_TO_WH
    else:
        return value

    if unit is None:
        return value
    factor = table.get(unit)
    if factor is None:
        _LOGGER.debug(
            "Unknown unit %r for field %s; passing value through unchanged",
            unit,
            key,
        )
        return value
    return value * factor


class EcotrackerJsonView(HomeAssistantView):
    url = API_PATH
    name = "ecotracker_emulator:json"
    requires_auth = False

    async def get(self, request):
        hass: HomeAssistant = request.app["hass"]
        entry = self._get_entry(hass)
        if not entry:
            return self.json({"error": "not configured"}, status=500)

        options = entry.options
        data: dict[str, float | int] = {}

        for key in DEFAULT_VALUES:
            entity_id = options.get(f"{key}_entity")
            if entity_id:
                state = hass.states.get(entity_id)
                if state and state.state not in ("unknown", "unavailable"):
                    try:
                        raw = float(state.state)
                    except (ValueError, TypeError):
                        pass
                    else:
                        unit = state.attributes.get("unit_of_measurement")
                        data[key] = _convert(key, raw, unit)
                        continue
            data[key] = options.get(f"{key}_fallback", 0)

        return self.json(data)

    def _get_entry(self, hass: HomeAssistant):
        entries = hass.config_entries.async_entries(DOMAIN)
        return entries[0] if entries else None
