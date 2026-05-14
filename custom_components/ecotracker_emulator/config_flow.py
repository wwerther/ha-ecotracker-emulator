import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers import selector
from .const import DOMAIN, DEFAULT_VALUES

DATA_SCHEMA = vol.Schema({
    vol.Optional("service_name", default="ecotracker-B43A452249C9"): str,
    vol.Optional("port", default=8123): int,
})

class EcotrackerConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        # Nur eine Instanz erlauben - HA hoert nur auf einem Port und
        # /v1/json existiert global, mehrere Eintraege wuerden kollidieren.
        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")

        errors: dict[str, str] = {}
        if user_input is not None:
            await self.async_set_unique_id(DOMAIN)
            self._abort_if_unique_id_configured()

            return self.async_create_entry(
                title=user_input["service_name"],
                data=user_input,
                options={
                    # Hier spaeter die Sensor-Zuordnungen speichern
                    **{f"{key}_entity": None for key in DEFAULT_VALUES},
                    **{f"{key}_fallback": value for key, value in DEFAULT_VALUES.items()}
                }
            )
        return self.async_show_form(step_id="user", data_schema=DATA_SCHEMA, errors=errors)

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return EcotrackerOptionsFlow(config_entry)

class EcotrackerOptionsFlow(config_entries.OptionsFlow):
    def __init__(self, config_entry):
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        # Für die erste Version reicht ein Platzhalter
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)
        return self.async_show_form(step_id="init")