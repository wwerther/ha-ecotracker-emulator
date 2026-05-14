import logging
import socket

import zeroconf as zc
from homeassistant.components import network, zeroconf
from homeassistant.components.network.const import MDNS_TARGET_IP
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .api import EcotrackerJsonView
from .const import (
    CONF_LEGACY_SERVICE_NAME,
    CONF_MAC_SUFFIX,
    CONF_PORT,
    CONF_PRODUCT_ID,
    CONF_SERIAL,
    DEFAULT_PRODUCT_ID,
    DOMAIN,
    MDNS_PORT,
    MDNS_SERVICE_TYPE,
    SERVICE_NAME_PREFIX,
)

_LOGGER = logging.getLogger(__name__)


def _resolve_service_name(entry: ConfigEntry) -> str:
    """Build the full mDNS service name, supporting legacy entries."""
    mac_suffix = entry.data.get(CONF_MAC_SUFFIX)
    if mac_suffix:
        return f"{SERVICE_NAME_PREFIX}{mac_suffix}"
    legacy = entry.data.get(CONF_LEGACY_SERVICE_NAME)
    if legacy:
        return str(legacy)
    raise RuntimeError(
        "Config entry is missing both 'mac_suffix' and legacy 'service_name'"
    )


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    hass.data.setdefault(DOMAIN, {})

    # API View registrieren
    hass.http.register_view(EcotrackerJsonView)

    # mDNS Dienst publizieren und Handles für Cleanup speichern
    aiozc, service_info = await _publish_mdns_service(hass, entry)
    hass.data[DOMAIN][entry.entry_id] = {
        "entry": entry,
        "aiozc": aiozc,
        "service_info": service_info,
    }

    # Options-Update abfangen
    entry.async_on_unload(entry.add_update_listener(_async_update_listener))

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    data = hass.data.get(DOMAIN, {}).pop(entry.entry_id, None)
    if data is not None:
        aiozc = data.get("aiozc")
        service_info = data.get("service_info")
        if aiozc is not None and service_info is not None:
            try:
                await aiozc.async_unregister_service(service_info)
            except Exception:  # noqa: BLE001 - cleanup must not fail unload
                _LOGGER.exception(
                    "Failed to unregister mDNS service %s", service_info.name
                )

    if not hass.data.get(DOMAIN):
        hass.data.pop(DOMAIN, None)

    return True


async def _publish_mdns_service(
    hass: HomeAssistant, entry: ConfigEntry
) -> tuple[object, zc.ServiceInfo]:
    aiozc = await zeroconf.async_get_async_instance(hass)
    service_name = f"{_resolve_service_name(entry)}.{MDNS_SERVICE_TYPE}"
    port = entry.data.get(CONF_PORT, MDNS_PORT)

    local_ip = await network.async_get_source_ip(hass, MDNS_TARGET_IP)
    if not local_ip:
        # Ohne routebare IP waere die mDNS-Bekanntmachung wertlos
        raise RuntimeError(
            "Cannot determine a routable local IP for mDNS publication"
        )

    properties = {
        "ip": local_ip,
        "serial": entry.data.get(CONF_SERIAL, "a5e235f42c75"),
        "productid": entry.data.get(CONF_PRODUCT_ID, DEFAULT_PRODUCT_ID),
    }

    service_info = zc.ServiceInfo(
        MDNS_SERVICE_TYPE,
        service_name,
        addresses=[socket.inet_aton(local_ip)],
        port=port,
        properties=properties,
    )
    await aiozc.async_register_service(service_info)
    _LOGGER.info(
        "Registered mDNS service %s on %s:%s", service_name, local_ip, port
    )
    return aiozc, service_info


async def _async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Wird aufgerufen, wenn die Optionen geaendert werden."""
    await hass.config_entries.async_reload(entry.entry_id)