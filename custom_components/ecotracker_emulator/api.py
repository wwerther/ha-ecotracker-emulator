from aiohttp import web
from homeassistant.components.http import HomeAssistantView
from homeassistant.core import HomeAssistant
from .const import DOMAIN, API_PATH

class EcotrackerJsonView(HomeAssistantView):
    url = API_PATH
    name = "ecotracker_emulator:json"
    requires_auth = False

    async def get(self, request):
        hass = request.app["hass"]
        # Config-Eintrag finden
        entry = self._get_entry(hass)
        if not entry:
            return self.json({"error": "not configured"}, status=500)

        options = entry.options
        data = {}

        for key in ["power", "powerAvg", "agePower", "powerPhase1", "powerPhase2", "powerPhase3", "energyCounterOut", "energyCounterIn"]:
            entity_id = options.get(f"{key}_entity")
            if entity_id:
                state = hass.states.get(entity_id)
                if state and state.state not in ("unknown", "unavailable"):
                    try:
                        data[key] = float(state.state)
                        continue
                    except (ValueError, TypeError):
                        pass
            # Fallback
            data[key] = options.get(f"{key}_fallback", 0)

        return self.json(data)

    def _get_entry(self, hass: HomeAssistant):
        entries = hass.config_entries.async_entries(DOMAIN)
        return entries[0] if entries else None