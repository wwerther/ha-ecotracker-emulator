"""Config + options flow for the EcoTracker emulator."""
from __future__ import annotations

import re
import secrets
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers.selector import (
    EntitySelector,
    EntitySelectorConfig,
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
)

from .const import (
    CONF_MAC_SUFFIX,
    CONF_PORT,
    CONF_PRODUCT_ID,
    CONF_SERIAL,
    DEFAULT_PRODUCT_ID,
    DEFAULT_VALUES,
    DOMAIN,
    MAC_OUI,
    MDNS_PORT,
    SERVICE_NAME_PREFIX,
)

# Per-field hints used to narrow down the sensor picker. `device_class` is the
# preferred filter; `units` catches sensors that lack a device_class (typical
# for hand-rolled template sensors). `None`/empty = no filter (e.g. agePower).
_FIELD_DEVICE_CLASS: dict[str, str | None] = {
    "power": "power",
    "powerAvg": "power",
    "powerPhase1": "power",
    "powerPhase2": "power",
    "powerPhase3": "power",
    "energyCounterIn": "energy",
    "energyCounterOut": "energy",
    "agePower": None,
}
_FIELD_UNITS: dict[str, tuple[str, ...]] = {
    "power": ("W", "kW", "mW"),
    "powerAvg": ("W", "kW", "mW"),
    "powerPhase1": ("W", "kW", "mW"),
    "powerPhase2": ("W", "kW", "mW"),
    "powerPhase3": ("W", "kW", "mW"),
    "energyCounterIn": ("Wh", "kWh", "MWh"),
    "energyCounterOut": ("Wh", "kWh", "MWh"),
    "agePower": (),
}

CONF_SHOW_ALL_SENSORS = "show_all_sensors"

# 12 hex chars, no separators (= 6-byte MAC / serial)
_HEX12 = re.compile(r"^[0-9A-Fa-f]{12}$")


def _random_mac_suffix() -> str:
    """Build a MAC-formatted suffix using the EcoTracker OUI plus 6 random hex chars."""
    return (MAC_OUI + secrets.token_hex(3)).upper()


def _random_serial() -> str:
    """Random 12-hex-char serial, lowercase to match the real-device convention."""
    return secrets.token_hex(6).lower()


def _normalize_mac(value: str) -> str:
    """Strip separators, validate as 12 hex chars, return uppercase."""
    cleaned = re.sub(r"[\s:\-]", "", str(value))
    if not _HEX12.match(cleaned):
        raise vol.Invalid("invalid_mac_suffix")
    return cleaned.upper()


def _normalize_serial(value: str) -> str:
    """Validate serial as 12 hex chars, return lowercase."""
    cleaned = re.sub(r"[\s:\-]", "", str(value))
    if not _HEX12.match(cleaned):
        raise vol.Invalid("invalid_serial")
    return cleaned.lower()


def _build_schema(defaults: dict[str, Any]) -> vol.Schema:
    return vol.Schema(
        {
            vol.Required(CONF_MAC_SUFFIX, default=defaults[CONF_MAC_SUFFIX]): str,
            vol.Required(CONF_SERIAL, default=defaults[CONF_SERIAL]): str,
            vol.Required(CONF_PRODUCT_ID, default=defaults[CONF_PRODUCT_ID]): str,
            vol.Required(CONF_PORT, default=defaults[CONF_PORT]): int,
        }
    )


class EcotrackerConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None):
        # Only one instance allowed: HA only listens on a single port and
        # /v1/json is a global path, so multiple entries would collide.
        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")

        defaults: dict[str, Any] = {
            CONF_MAC_SUFFIX: _random_mac_suffix(),
            CONF_SERIAL: _random_serial(),
            CONF_PRODUCT_ID: DEFAULT_PRODUCT_ID,
            CONF_PORT: MDNS_PORT,
        }
        errors: dict[str, str] = {}

        if user_input is not None:
            mac_suffix = serial = ""
            try:
                mac_suffix = _normalize_mac(user_input[CONF_MAC_SUFFIX])
            except vol.Invalid:
                errors[CONF_MAC_SUFFIX] = "invalid_mac_suffix"
            try:
                serial = _normalize_serial(user_input[CONF_SERIAL])
            except vol.Invalid:
                errors[CONF_SERIAL] = "invalid_serial"

            product_id = str(user_input[CONF_PRODUCT_ID]).strip()
            if not product_id:
                errors[CONF_PRODUCT_ID] = "invalid_product_id"

            try:
                port = int(user_input[CONF_PORT])
            except (TypeError, ValueError):
                port = 0
            if not 1 <= port <= 65535:
                errors[CONF_PORT] = "invalid_port"

            if not errors:
                await self.async_set_unique_id(DOMAIN)
                self._abort_if_unique_id_configured()

                data = {
                    CONF_MAC_SUFFIX: mac_suffix,
                    CONF_SERIAL: serial,
                    CONF_PRODUCT_ID: product_id,
                    CONF_PORT: port,
                }
                return self.async_create_entry(
                    title=f"{SERVICE_NAME_PREFIX}{mac_suffix}",
                    data=data,
                    options={
                        # Sensor mappings are filled in via the options flow.
                        **{f"{key}_entity": None for key in DEFAULT_VALUES},
                        **{
                            f"{key}_fallback": value
                            for key, value in DEFAULT_VALUES.items()
                        },
                    },
                )

            # Re-show form with the user-entered values + errors.
            defaults = {**defaults, **user_input}

        return self.async_show_form(
            step_id="user",
            data_schema=_build_schema(defaults),
            errors=errors,
            description_placeholders={
                "prefix": SERVICE_NAME_PREFIX,
                "oui": MAC_OUI,
            },
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return EcotrackerOptionsFlow()


class EcotrackerOptionsFlow(config_entries.OptionsFlow):
    """Map each EcoTracker JSON field to a HA sensor entity or numeric fallback."""

    async def async_step_init(self, user_input: dict[str, Any] | None = None):
        current = dict(self.config_entry.options)
        show_all = bool(current.get(CONF_SHOW_ALL_SENSORS, False))

        if user_input is not None:
            # Persist all entity / fallback pairs. Empty entity selections come
            # back as missing keys; normalise to an explicit `None` so api.py's
            # `options.get(...)` keeps working as before.
            new_options: dict[str, Any] = {
                CONF_SHOW_ALL_SENSORS: bool(user_input.get(CONF_SHOW_ALL_SENSORS)),
            }
            for key in DEFAULT_VALUES:
                entity_key = f"{key}_entity"
                fallback_key = f"{key}_fallback"
                new_options[entity_key] = user_input.get(entity_key) or None
                new_options[fallback_key] = user_input[fallback_key]
            return self.async_create_entry(title="", data=new_options)

        schema_dict: dict[Any, Any] = {
            vol.Required(
                CONF_SHOW_ALL_SENSORS, default=show_all
            ): bool,
        }
        for key, default_value in DEFAULT_VALUES.items():
            entity_key = f"{key}_entity"
            fallback_key = f"{key}_fallback"
            current_entity = current.get(entity_key)
            current_fallback = current.get(fallback_key, default_value)

            entity_field = vol.Optional(
                entity_key,
                description={"suggested_value": current_entity}
                if current_entity
                else None,
            )
            schema_dict[entity_field] = EntitySelector(
                self._entity_selector_config(key, show_all=show_all)
            )
            schema_dict[
                vol.Required(fallback_key, default=current_fallback)
            ] = NumberSelector(
                NumberSelectorConfig(mode=NumberSelectorMode.BOX, step="any")
            )

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(schema_dict),
        )

    def _entity_selector_config(
        self, key: str, *, show_all: bool
    ) -> EntitySelectorConfig:
        """Build a sensor selector config: device_class + matching units.

        ``show_all=True`` disables filtering entirely (escape hatch for sensors
        that have neither a device_class nor a known unit). Otherwise we always
        keep the previously-selected entity in the list, even if it would be
        filtered out, so the current mapping stays visible.
        """
        if show_all or not _FIELD_DEVICE_CLASS.get(key):
            return EntitySelectorConfig(domain="sensor")

        units = set(_FIELD_UNITS.get(key, ()))
        # Walk all sensor states and accept those matching either device_class
        # or one of the known units; this catches template sensors that only
        # set unit_of_measurement.
        include: list[str] = []
        device_class = _FIELD_DEVICE_CLASS[key]
        for state in self.hass.states.async_all("sensor"):
            attrs = state.attributes
            if attrs.get("device_class") == device_class:
                include.append(state.entity_id)
                continue
            if units and attrs.get("unit_of_measurement") in units:
                include.append(state.entity_id)

        # Always keep the current pick visible, even if filtered out.
        current_entity = self.config_entry.options.get(f"{key}_entity")
        if current_entity and current_entity not in include:
            include.append(current_entity)

        if not include:
            # No matches at all: fall back to device_class-only filter so the
            # picker stays usable instead of returning an empty list.
            return EntitySelectorConfig(
                domain="sensor", device_class=device_class
            )
        return EntitySelectorConfig(include_entities=include)
