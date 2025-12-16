"""Data update coordinator for LubeLogger."""
from __future__ import annotations

import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .client import LubeLoggerClient
from .const import (
    CONF_PASSWORD,
    CONF_URL,
    CONF_USERNAME,
    DEFAULT_UPDATE_INTERVAL,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)


class LubeLoggerDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching LubeLogger data."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize the coordinator."""
        self.entry = entry
        self.client = LubeLoggerClient(
            url=entry.data[CONF_URL],
            username=entry.data[CONF_USERNAME],
            password=entry.data[CONF_PASSWORD],
        )

        update_interval = timedelta(
            seconds=entry.options.get("update_interval", DEFAULT_UPDATE_INTERVAL)
        )

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=update_interval,
        )

    async def _async_update_data(self) -> dict:
        """Fetch data from LubeLogger."""
        try:
            vehicles = await self.client.async_get_vehicles()
            data = {"vehicles": vehicles}

            # Fetch additional data for each vehicle
            for vehicle in vehicles:
                vehicle_id = vehicle.get("id")
                if vehicle_id:
                    try:
                        # Get statistics for each vehicle
                        stats = await self.client.async_get_vehicle_statistics(
                            vehicle_id
                        )
                        vehicle["statistics"] = stats

                        # Get recent maintenance records
                        maintenance = await self.client.async_get_maintenance_records(
                            vehicle_id
                        )
                        vehicle["maintenance"] = maintenance

                        # Get recent fuel records
                        fuel = await self.client.async_get_fuel_records(vehicle_id)
                        vehicle["fuel"] = fuel
                    except Exception as err:
                        _LOGGER.warning(
                            "Error fetching data for vehicle %s: %s", vehicle_id, err
                        )

            return data
        except Exception as err:
            raise UpdateFailed(f"Error communicating with LubeLogger: {err}") from err

