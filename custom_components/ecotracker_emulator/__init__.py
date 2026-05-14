import socket
import zeroconf as zc
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.components import zeroconf
from .const import DOMAIN, MDNS_SERVICE_TYPE, MDNS_PORT
from .api import EcotrackerJsonView

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = entry

    # API View registrieren
    hass.http.register_view(EcotrackerJsonView)

    # mDNS Dienst publizieren
    await _publish_mdns_service(hass, entry)

    # Options-Update abfangen
    entry.async_on_unload(entry.add_update_listener(_async_update_listener))

    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    # Hier später den mDNS Dienst deregistrieren
    return True

async def _publish_mdns_service(hass: HomeAssistant, entry: ConfigEntry):
    aiozc = await zeroconf.async_get_async_instance(hass)
    service_name = f"{entry.data['service_name']}.{MDNS_SERVICE_TYPE}"
    port = entry.data.get("port", MDNS_PORT)

    properties = {
        "ip": hass.config.api.local_ip,
        "serial": "a5e235f42c75",   # statisch – später konfigurierbar
        "productid": "1137"
    }

    service_info = zc.ServiceInfo(
        MDNS_SERVICE_TYPE,
        service_name,
        addresses=[socket.inet_aton(hass.config.api.local_ip)],
        port=port,
        properties=properties,
    )
    await aiozc.async_register_service(service_info)
    # ServiceInfo speichern, um später zu deregistrieren (in async_unload_entry)

async def _async_update_listener(hass: HomeAssistant, entry: ConfigEntry):
    """Wird aufgerufen, wenn die Optionen geändert werden."""
    await hass.config_entries.async_reload(entry.entry_id)