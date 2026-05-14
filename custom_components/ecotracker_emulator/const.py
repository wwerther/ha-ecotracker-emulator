DOMAIN = "ecotracker_emulator"
DEFAULT_NAME = "EcoTracker Emulator"

# mDNS Konfiguration
MDNS_SERVICE_TYPE = "_everhome._tcp.local."
MDNS_PORT = 8123

# Service-Name = SERVICE_NAME_PREFIX + MAC (12 Hex, uppercase, ohne Trenner)
# OUI ist der herstellerspezifische Teil; B4:3A:45 ist die OUI realer EcoTracker-Geraete.
SERVICE_NAME_PREFIX = "ecotracker-"
MAC_OUI = "B43A45"

# Default-Produkt-ID (als TXT-Record), entspricht beobachtetem Realgeraet.
DEFAULT_PRODUCT_ID = "1137"

# Konfigurationsschluessel in entry.data
CONF_MAC_SUFFIX = "mac_suffix"
CONF_SERIAL = "serial"
CONF_PRODUCT_ID = "product_id"
CONF_PORT = "port"
# Legacy-Key (wurde fuer Setups vor 2026-05-14 verwendet)
CONF_LEGACY_SERVICE_NAME = "service_name"

# API Pfad
API_PATH = "/v1/json"

# Standard-Fallback-Werte (falls keine Sensoren gewählt)
DEFAULT_VALUES = {
    "power": 0,
    "powerAvg": 0,
    "agePower": 0,
    "powerPhase1": 0,
    "powerPhase2": 0,
    "powerPhase3": 0,
    "energyCounterOut": 0,
    "energyCounterIn": 0
}