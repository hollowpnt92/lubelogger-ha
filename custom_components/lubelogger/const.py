"""Constants for the LubeLogger integration."""
from typing import Final

DOMAIN: Final = "lubelogger"

CONF_URL: Final = "url"
CONF_USERNAME: Final = "username"
CONF_PASSWORD: Final = "password"
CONF_UPDATE_INTERVAL: Final = "update_interval"

DEFAULT_UPDATE_INTERVAL: Final = 300  # 5 minutes

# API endpoints
# The LubeLogger API is rooted at /api and exposes multiple resources such as
# Odometer, Fuel, ServiceRecord, etc. Full docs are at /api.
# For now we only ping the root to verify connectivity; detailed endpoints
# can be wired up later once the desired data model is decided.
API_ROOT: Final = "/api"


