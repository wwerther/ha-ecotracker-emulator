"""Config + options flow for the EcoTracker emulator."""
from __future__ import annotations

import re
import secrets
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback

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
        return EcotrackerOptionsFlow(config_entry)


class EcotrackerOptionsFlow(config_entries.OptionsFlow):
    def __init__(self, config_entry):
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        # Placeholder until the entity-mapping UI is built (see TODO.md).
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)
        return self.async_show_form(step_id="init")
