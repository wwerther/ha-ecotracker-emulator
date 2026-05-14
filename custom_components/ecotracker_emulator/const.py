DOMAIN = "ecotracker_emulator"
DEFAULT_NAME = "EcoTracker Emulator"

# mDNS Konfiguration
MDNS_SERVICE_TYPE = "_everhome._tcp.local."
MDNS_SERVICE_NAME = "ecotracker-B43A452249C9"  # Kann später konfigurierbar sein
MDNS_PORT = 8123

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