"""Constants for the LubeLogger integration."""
from typing import Final

DOMAIN: Final = "lubelogger"

CONF_URL: Final = "url"
CONF_USERNAME: Final = "username"
CONF_PASSWORD: Final = "password"
CONF_UPDATE_INTERVAL: Final = "update_interval"

DEFAULT_UPDATE_INTERVAL: Final = 300  # 5 minutes

# API endpoints (these may need to be adjusted based on actual LubeLogger API)
API_VEHICLES: Final = "/api/Vehicle/GetAllVehicles"
API_MAINTENANCE: Final = "/api/MaintenanceRecord/GetAllMaintenanceRecords"
API_FUEL: Final = "/api/GasRecord/GetAllGasRecords"
API_STATS: Final = "/api/Vehicle/GetVehicleStatistics"

