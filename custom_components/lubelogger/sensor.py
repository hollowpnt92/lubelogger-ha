"""Sensor platform for LubeLogger integration."""
from __future__ import annotations

from datetime import datetime
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import dt as dt_util

from .coordinator import LubeLoggerDataUpdateCoordinator


def parse_date(date_str: str | None) -> datetime | None:
    """Parse a date string from LubeLogger API."""
    if not date_str:
        return None
    
    # Try ISO format first
    try:
        # Handle Z suffix and convert to UTC
        if date_str.endswith("Z"):
            date_str = date_str.replace("Z", "+00:00")
        return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        pass
    
    # Try common date formats
    formats = [
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%dT%H:%M:%S.%f",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d",
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except (ValueError, AttributeError):
            continue
    
    return None


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up LubeLogger sensors from a config entry."""
    coordinator: LubeLoggerDataUpdateCoordinator = hass.data["lubelogger"][
        entry.entry_id
    ]

    sensors = []
    vehicles = coordinator.data.get("vehicles", [])

    for vehicle in vehicles:
        vehicle_id = vehicle.get("id")
        vehicle_name = vehicle.get("name", f"Vehicle {vehicle_id}")

        # Vehicle statistics sensors
        stats = vehicle.get("statistics", {})
        if stats:
            sensors.append(
                LubeLoggerSensor(
                    coordinator,
                    vehicle_id,
                    vehicle_name,
                    "total_miles",
                    "Total Miles",
                    "miles",
                    SensorDeviceClass.DISTANCE,
                    SensorStateClass.TOTAL_INCREASING,
                )
            )
            sensors.append(
                LubeLoggerSensor(
                    coordinator,
                    vehicle_id,
                    vehicle_name,
                    "average_mpg",
                    "Average MPG",
                    "mpg",
                    None,
                    SensorStateClass.MEASUREMENT,
                )
            )
            sensors.append(
                LubeLoggerSensor(
                    coordinator,
                    vehicle_id,
                    vehicle_name,
                    "total_fuel_cost",
                    "Total Fuel Cost",
                    "USD",
                    SensorDeviceClass.MONETARY,
                    SensorStateClass.TOTAL_INCREASING,
                )
            )

        # Maintenance sensors
        maintenance = vehicle.get("maintenance", [])
        if maintenance:
            # Next maintenance due
            sensors.append(
                LubeLoggerMaintenanceSensor(
                    coordinator,
                    vehicle_id,
                    vehicle_name,
                    "next_maintenance",
                    "Next Maintenance Due",
                )
            )
            # Last maintenance date
            sensors.append(
                LubeLoggerMaintenanceSensor(
                    coordinator,
                    vehicle_id,
                    vehicle_name,
                    "last_maintenance",
                    "Last Maintenance",
                )
            )

        # Fuel sensors
        fuel = vehicle.get("fuel", [])
        if fuel:
            # Last fuel fill date
            sensors.append(
                LubeLoggerFuelSensor(
                    coordinator,
                    vehicle_id,
                    vehicle_name,
                    "last_fuel_fill",
                    "Last Fuel Fill",
                )
            )
            # Last fuel price
            sensors.append(
                LubeLoggerFuelSensor(
                    coordinator,
                    vehicle_id,
                    vehicle_name,
                    "last_fuel_price",
                    "Last Fuel Price",
                    SensorDeviceClass.MONETARY,
                )
            )

    async_add_entities(sensors)


class LubeLoggerSensor(CoordinatorEntity, SensorEntity):
    """Base sensor for LubeLogger vehicle data."""

    def __init__(
        self,
        coordinator: LubeLoggerDataUpdateCoordinator,
        vehicle_id: int,
        vehicle_name: str,
        sensor_key: str,
        sensor_name: str,
        unit: str | None,
        device_class: SensorDeviceClass | None = None,
        state_class: SensorStateClass | None = None,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._vehicle_id = vehicle_id
        self._vehicle_name = vehicle_name
        self._sensor_key = sensor_key
        self._attr_name = f"{vehicle_name} {sensor_name}"
        self._attr_unique_id = f"lubelogger_{vehicle_id}_{sensor_key}"
        self._attr_native_unit_of_measurement = unit
        self._attr_device_class = device_class
        self._attr_state_class = state_class

    @property
    def native_value(self) -> Any:
        """Return the state of the sensor."""
        vehicles = self.coordinator.data.get("vehicles", [])
        for vehicle in vehicles:
            if vehicle.get("id") == self._vehicle_id:
                stats = vehicle.get("statistics", {})
                return stats.get(self._sensor_key)

        return None


class LubeLoggerMaintenanceSensor(CoordinatorEntity, SensorEntity):
    """Sensor for maintenance records."""

    def __init__(
        self,
        coordinator: LubeLoggerDataUpdateCoordinator,
        vehicle_id: int,
        vehicle_name: str,
        sensor_type: str,
        sensor_name: str,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._vehicle_id = vehicle_id
        self._vehicle_name = vehicle_name
        self._sensor_type = sensor_type
        self._attr_name = f"{vehicle_name} {sensor_name}"
        self._attr_unique_id = f"lubelogger_{vehicle_id}_{sensor_type}"
        self._attr_device_class = SensorDeviceClass.TIMESTAMP

    @property
    def native_value(self) -> datetime | None:
        """Return the state of the sensor."""
        vehicles = self.coordinator.data.get("vehicles", [])
        for vehicle in vehicles:
            if vehicle.get("id") == self._vehicle_id:
                maintenance = vehicle.get("maintenance", [])
                if not maintenance:
                    return None

                if self._sensor_type == "next_maintenance":
                    # Find the next upcoming maintenance
                    now = dt_util.now()
                    upcoming = []
                    for m in maintenance:
                        date_obj = parse_date(m.get("date"))
                        if date_obj and date_obj > now:
                            upcoming.append((m, date_obj))
                    
                    if upcoming:
                        next_maint, _ = min(upcoming, key=lambda x: x[1])
                        return parse_date(next_maint.get("date"))
                elif self._sensor_type == "last_maintenance":
                    # Find the most recent maintenance
                    past = []
                    for m in maintenance:
                        date_obj = parse_date(m.get("date"))
                        if date_obj and date_obj <= now:
                            past.append((m, date_obj))
                    
                    if past:
                        last_maint, _ = max(past, key=lambda x: x[1])
                        return parse_date(last_maint.get("date"))

        return None


class LubeLoggerFuelSensor(CoordinatorEntity, SensorEntity):
    """Sensor for fuel records."""

    def __init__(
        self,
        coordinator: LubeLoggerDataUpdateCoordinator,
        vehicle_id: int,
        vehicle_name: str,
        sensor_type: str,
        sensor_name: str,
        device_class: SensorDeviceClass | None = None,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._vehicle_id = vehicle_id
        self._vehicle_name = vehicle_name
        self._sensor_type = sensor_type
        self._attr_name = f"{vehicle_name} {sensor_name}"
        self._attr_unique_id = f"lubelogger_{vehicle_id}_{sensor_type}"
        self._attr_device_class = device_class

    @property
    def native_value(self) -> Any:
        """Return the state of the sensor."""
        vehicles = self.coordinator.data.get("vehicles", [])
        for vehicle in vehicles:
            if vehicle.get("id") == self._vehicle_id:
                fuel = vehicle.get("fuel", [])
                if not fuel:
                    return None

                # Sort by date, most recent first
                fuel_with_dates = []
                for f in fuel:
                    date_obj = parse_date(f.get("date"))
                    if date_obj:
                        fuel_with_dates.append((f, date_obj))
                
                if fuel_with_dates:
                    fuel_with_dates.sort(key=lambda x: x[1], reverse=True)
                    last_fuel = fuel_with_dates[0][0]
                    
                    if self._sensor_type == "last_fuel_fill":
                        self._attr_device_class = SensorDeviceClass.TIMESTAMP
                        return parse_date(last_fuel.get("date"))
                    elif self._sensor_type == "last_fuel_price":
                        self._attr_native_unit_of_measurement = "USD"
                        return last_fuel.get("costPerGallon") or last_fuel.get("price")

        return None

