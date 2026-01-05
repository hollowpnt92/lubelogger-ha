"""Constants for the LubeLogger integration."""
from typing import Final

DOMAIN: Final = "lubelogger"

CONF_URL: Final = "url"
CONF_USERNAME: Final = "username"
CONF_PASSWORD: Final = "password"
CONF_UPDATE_INTERVAL: Final = "update_interval"

DEFAULT_UPDATE_INTERVAL: Final = 300  # 5 minutes

# API endpoints
# The LubeLogger API is rooted at /api and exposes multiple resources.
# See https://docs.lubelogger.com/Advanced/API for details.
API_ROOT: Final = "/api"
API_VEHICLES: Final = "/api/vehicles"

# Vehicle-scoped endpoints
API_ODOMETER: Final = "/api/vehicle/odometerrecords"
API_ADJUSTED_ODOMETER: Final = "/api/vehicle/adjustedodometer"
API_PLAN: Final = "/api/vehicle/planrecords"
API_TAX: Final = "/api/vehicle/taxrecords"
API_SERVICE_RECORD: Final = "/api/vehicle/servicerecords"
API_REPAIR_RECORD: Final = "/api/vehicle/repairrecords"
API_UPGRADE_RECORD: Final = "/api/vehicle/upgraderecords"
API_SUPPLY_RECORD: Final = "/api/vehicle/supplyrecords"
API_GAS_RECORD: Final = "/api/vehicle/gasrecords"
API_REMINDER: Final = "/api/vehicle/reminders"


