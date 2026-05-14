import logging
import socket

import zeroconf as zc
from homeassistant.components import network, zeroconf
from homeassistant.components.network.const import MDNS_TARGET_IP
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .api import EcotrackerJsonView
from .const import DOMAIN, MDNS_PORT, MDNS_SERVICE_TYPE

_LOGGER = logging.getLogger(__name__)


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
    service_name = f"{entry.data['service_name']}.{MDNS_SERVICE_TYPE}"
    port = entry.data.get("port", MDNS_PORT)

    local_ip = await network.async_get_source_ip(hass, MDNS_TARGET_IP)
    if not local_ip:
        # Ohne routebare IP waere die mDNS-Bekanntmachung wertlos
        raise RuntimeError(
            "Cannot determine a routable local IP for mDNS publication"
        )

    properties = {
        "ip": local_ip,
        "serial": "a5e235f42c75",  # statisch - spaeter konfigurierbar
        "productid": "1137",
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