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
        """Fetch data from LubeLogger, organized by vehicle."""
        data: dict = {"vehicles": []}

        # Get all vehicles
        try:
            vehicles = await self.client.async_get_vehicles()
        except Exception as err:
            _LOGGER.warning("Error fetching vehicles: %s", err)
            return data

        # For each vehicle, fetch its specific data
        for vehicle in vehicles:
            vehicle_id = vehicle.get("Id") or vehicle.get("id")
            if not vehicle_id:
                continue

            # Build device name from Make, Model, Year
            make = vehicle.get("Make") or vehicle.get("make") or ""
            model = vehicle.get("Model") or vehicle.get("model") or ""
            year = vehicle.get("Year") or vehicle.get("year") or ""
            
            name_parts = [part for part in [year, make, model] if part]
            device_name = " ".join(name_parts) if name_parts else vehicle.get("Name") or vehicle.get("name") or f"Vehicle {vehicle_id}"

            vehicle_data = {
                "id": vehicle_id,
                "name": device_name,
                "vehicle_info": vehicle,
            }

            # Latest odometer for this vehicle
            try:
                vehicle_data["latest_odometer"] = await self.client.async_get_latest_odometer(
                    vehicle_id
                )
            except Exception as err:
                _LOGGER.warning(
                    "Error fetching latest odometer for vehicle %s: %s", vehicle_id, err
                )
                vehicle_data["latest_odometer"] = None

            # Next planned item for this vehicle
            try:
                vehicle_data["next_plan"] = await self.client.async_get_next_plan(vehicle_id)
            except Exception as err:
                _LOGGER.warning(
                    "Error fetching next plan for vehicle %s: %s", vehicle_id, err
                )
                vehicle_data["next_plan"] = None

            # Latest tax for this vehicle
            try:
                vehicle_data["latest_tax"] = await self.client.async_get_latest_tax(vehicle_id)
            except Exception as err:
                _LOGGER.warning(
                    "Error fetching latest tax for vehicle %s: %s", vehicle_id, err
                )
                vehicle_data["latest_tax"] = None

            # Latest service record for this vehicle
            try:
                vehicle_data["latest_service"] = await self.client.async_get_latest_service(
                    vehicle_id
                )
            except Exception as err:
                _LOGGER.warning(
                    "Error fetching latest service for vehicle %s: %s", vehicle_id, err
                )
                vehicle_data["latest_service"] = None

            data["vehicles"].append(vehicle_data)

        return data

