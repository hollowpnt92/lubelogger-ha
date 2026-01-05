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
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import dt as dt_util

from .const import DOMAIN
from .coordinator import LubeLoggerDataUpdateCoordinator


def parse_date(date_str: str | None) -> datetime | None:
    """Parse a date string from LubeLogger API and return timezone-aware datetime."""
    if not date_str:
        return None

    # Try ISO format first
    try:
        if date_str.endswith("Z"):
            date_str = date_str.replace("Z", "+00:00")
        dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        # Ensure timezone-aware
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=dt_util.UTC)
        return dt
    except (ValueError, AttributeError):
        pass

    # Try common date formats (including MM/DD/YYYY from LubeLogger API)
    formats = [
        "%m/%d/%Y",  # LubeLogger format: "12/17/2025"
        "%m/%d/%Y %H:%M:%S",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%dT%H:%M:%S.%f",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d",
    ]

    for fmt in formats:
        try:
            dt = datetime.strptime(date_str, fmt)
            # Make timezone-aware (assume local timezone)
            if dt.tzinfo is None:
                dt = dt_util.as_local(dt)
            return dt
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

    sensors: list[SensorEntity] = []
    vehicles = coordinator.data.get("vehicles", [])

    for vehicle in vehicles:
        vehicle_id = vehicle.get("id")
        vehicle_name = vehicle.get("name", f"Vehicle {vehicle_id}")
        vehicle_info = vehicle.get("vehicle_info", {})

        # Only create sensors if data exists (visible/tabs requirement)
        if vehicle.get("latest_odometer"):
            sensors.append(
                LubeLoggerLatestOdometerSensor(coordinator, vehicle_id, vehicle_name, vehicle_info)
            )
        if vehicle.get("next_plan"):
            sensors.append(
                LubeLoggerNextPlanSensor(coordinator, vehicle_id, vehicle_name, vehicle_info)
            )
        if vehicle.get("latest_tax"):
            sensors.append(
                LubeLoggerLatestTaxSensor(coordinator, vehicle_id, vehicle_name, vehicle_info)
            )
        if vehicle.get("latest_service"):
            sensors.append(
                LubeLoggerLatestServiceSensor(coordinator, vehicle_id, vehicle_name, vehicle_info)
            )
        if vehicle.get("latest_repair"):
            sensors.append(
                LubeLoggerLatestRepairSensor(coordinator, vehicle_id, vehicle_name, vehicle_info)
            )
        if vehicle.get("latest_upgrade"):
            sensors.append(
                LubeLoggerLatestUpgradeSensor(coordinator, vehicle_id, vehicle_name, vehicle_info)
            )
        if vehicle.get("latest_supply"):
            sensors.append(
                LubeLoggerLatestSupplySensor(coordinator, vehicle_id, vehicle_name, vehicle_info)
            )
        if vehicle.get("latest_gas"):
            sensors.append(
                LubeLoggerLatestGasSensor(coordinator, vehicle_id, vehicle_name, vehicle_info)
            )
        if vehicle.get("next_reminder"):
            sensors.append(
                LubeLoggerNextReminderSensor(coordinator, vehicle_id, vehicle_name, vehicle_info)
            )

    async_add_entities(sensors)


class BaseLubeLoggerSensor(CoordinatorEntity, SensorEntity):
    """Base sensor that reads a key from coordinator data for a specific vehicle."""

    def __init__(
        self,
        coordinator: LubeLoggerDataUpdateCoordinator,
        vehicle_id: int,
        vehicle_name: str,
        vehicle_info: dict,
        key: str,
        sensor_name: str,
        unique_id_suffix: str,
        device_class: SensorDeviceClass | None = None,
        state_class: SensorStateClass | None = None,
        unit: str | None = None,
    ) -> None:
        super().__init__(coordinator)
        self._vehicle_id = vehicle_id
        self._vehicle_name = vehicle_name
        self._key = key
        self._attr_name = f"{vehicle_name} {sensor_name}"
        self._attr_unique_id = f"lubelogger_{vehicle_id}_{unique_id_suffix}"
        self._attr_device_class = device_class
        self._attr_state_class = state_class
        self._attr_native_unit_of_measurement = unit
        
        # Extract make/model/year from vehicle info for device info
        make = vehicle_info.get("Make") or vehicle_info.get("make") or ""
        model = vehicle_info.get("Model") or vehicle_info.get("model") or ""
        year = str(vehicle_info.get("Year") or vehicle_info.get("year") or "")
        
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, str(vehicle_id))},
            name=vehicle_name,
            manufacturer=make or "LubeLogger",
            model=model or vehicle_name,
            sw_version=year,
        )

    @property
    def _record(self) -> dict | None:
        data = self.coordinator.data or {}
        vehicles = data.get("vehicles", [])
        for vehicle in vehicles:
            if vehicle.get("id") == self._vehicle_id:
                rec = vehicle.get(self._key)
                return rec if isinstance(rec, dict) else None
        return None

    @property
    def available(self) -> bool:
        """Return if sensor is available."""
        return self._record is not None


class LubeLoggerLatestOdometerSensor(BaseLubeLoggerSensor):
    """Sensor for latest odometer value."""

    def __init__(
        self,
        coordinator: LubeLoggerDataUpdateCoordinator,
        vehicle_id: int,
        vehicle_name: str,
        vehicle_info: dict,
    ) -> None:
        super().__init__(
            coordinator,
            vehicle_id,
            vehicle_name,
            vehicle_info,
            key="latest_odometer",
            sensor_name="Latest Odometer",
            unique_id_suffix="latest_odometer",
            device_class=SensorDeviceClass.DISTANCE,
            state_class=SensorStateClass.MEASUREMENT,
            unit="mi",
        )

    @property
    def native_value(self) -> Any:
        rec = self._record
        if not rec:
            return None
        # Adjusted odometer endpoint returns the value directly
        if rec.get("adjusted"):
            odometer = rec.get("odometer")
        else:
            # API returns lowercase 'odometer' field from records
            odometer = rec.get("odometer") or rec.get("Odometer")
        
        if odometer:
            try:
                return int(odometer)
            except (ValueError, TypeError):
                try:
                    return float(odometer)
                except (ValueError, TypeError):
                    return odometer
        return None

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        return self._record or None


class LubeLoggerNextPlanSensor(BaseLubeLoggerSensor):
    """Sensor for next planned item from Plan endpoint."""

    def __init__(
        self,
        coordinator: LubeLoggerDataUpdateCoordinator,
        vehicle_id: int,
        vehicle_name: str,
        vehicle_info: dict,
    ) -> None:
        super().__init__(
            coordinator,
            vehicle_id,
            vehicle_name,
            vehicle_info,
            key="next_plan",
            sensor_name="Next Plan",
            unique_id_suffix="next_plan",
            device_class=SensorDeviceClass.TIMESTAMP,
        )

    @property
    def native_value(self) -> datetime | None:
        rec = self._record
        if not rec:
            return None

        # API uses dateCreated or dateModified for plan records
        for field in ("dateCreated", "dateModified", "Date", "date"):
            dt = parse_date(rec.get(field))
            if dt:
                return dt
        return None

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        return self._record or None


class LubeLoggerLatestTaxSensor(BaseLubeLoggerSensor):
    """Sensor for latest tax record."""

    def __init__(
        self,
        coordinator: LubeLoggerDataUpdateCoordinator,
        vehicle_id: int,
        vehicle_name: str,
        vehicle_info: dict,
    ) -> None:
        super().__init__(
            coordinator,
            vehicle_id,
            vehicle_name,
            vehicle_info,
            key="latest_tax",
            sensor_name="Latest Tax",
            unique_id_suffix="latest_tax",
            device_class=SensorDeviceClass.MONETARY,
            state_class=None,
            unit="USD",
        )

    @property
    def native_value(self) -> Any:
        rec = self._record
        if not rec:
            return None
        # API returns lowercase 'cost' field as string
        cost = rec.get("cost") or rec.get("Cost")
        if cost:
            try:
                return float(cost)
            except (ValueError, TypeError):
                return cost
        return None

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        return self._record or None


class LubeLoggerLatestServiceSensor(BaseLubeLoggerSensor):
    """Sensor for latest service record."""

    def __init__(
        self,
        coordinator: LubeLoggerDataUpdateCoordinator,
        vehicle_id: int,
        vehicle_name: str,
        vehicle_info: dict,
    ) -> None:
        super().__init__(
            coordinator,
            vehicle_id,
            vehicle_name,
            vehicle_info,
            key="latest_service",
            sensor_name="Latest Service",
            unique_id_suffix="latest_service",
            device_class=SensorDeviceClass.TIMESTAMP,
        )

    @property
    def native_value(self) -> datetime | None:
        rec = self._record
        if not rec:
            return None

        # API uses lowercase 'date' field
        for field in ("date", "Date", "ServiceDate"):
            dt = parse_date(rec.get(field))
            if dt:
                return dt
        return None

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        return self._record or None


class LubeLoggerLatestRepairSensor(BaseLubeLoggerSensor):
    """Sensor for latest repair record."""

    def __init__(
        self,
        coordinator: LubeLoggerDataUpdateCoordinator,
        vehicle_id: int,
        vehicle_name: str,
        vehicle_info: dict,
    ) -> None:
        super().__init__(
            coordinator,
            vehicle_id,
            vehicle_name,
            vehicle_info,
            key="latest_repair",
            sensor_name="Latest Repair",
            unique_id_suffix="latest_repair",
            device_class=SensorDeviceClass.TIMESTAMP,
        )

    @property
    def native_value(self) -> datetime | None:
        rec = self._record
        if not rec:
            return None

        for field in ("date", "Date", "RepairDate"):
            dt = parse_date(rec.get(field))
            if dt:
                return dt
        return None

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        return self._record or None


class LubeLoggerLatestUpgradeSensor(BaseLubeLoggerSensor):
    """Sensor for latest upgrade record."""

    def __init__(
        self,
        coordinator: LubeLoggerDataUpdateCoordinator,
        vehicle_id: int,
        vehicle_name: str,
        vehicle_info: dict,
    ) -> None:
        super().__init__(
            coordinator,
            vehicle_id,
            vehicle_name,
            vehicle_info,
            key="latest_upgrade",
            sensor_name="Latest Upgrade",
            unique_id_suffix="latest_upgrade",
            device_class=SensorDeviceClass.TIMESTAMP,
        )

    @property
    def native_value(self) -> datetime | None:
        rec = self._record
        if not rec:
            return None

        for field in ("date", "Date", "UpgradeDate"):
            dt = parse_date(rec.get(field))
            if dt:
                return dt
        return None

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        return self._record or None


class LubeLoggerLatestSupplySensor(BaseLubeLoggerSensor):
    """Sensor for latest supply record."""

    def __init__(
        self,
        coordinator: LubeLoggerDataUpdateCoordinator,
        vehicle_id: int,
        vehicle_name: str,
        vehicle_info: dict,
    ) -> None:
        super().__init__(
            coordinator,
            vehicle_id,
            vehicle_name,
            vehicle_info,
            key="latest_supply",
            sensor_name="Latest Supply",
            unique_id_suffix="latest_supply",
            device_class=SensorDeviceClass.TIMESTAMP,
        )

    @property
    def native_value(self) -> datetime | None:
        rec = self._record
        if not rec:
            return None

        for field in ("date", "Date", "SupplyDate"):
            dt = parse_date(rec.get(field))
            if dt:
                return dt
        return None

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        return self._record or None


class LubeLoggerLatestGasSensor(BaseLubeLoggerSensor):
    """Sensor for latest gas/fuel record."""

    def __init__(
        self,
        coordinator: LubeLoggerDataUpdateCoordinator,
        vehicle_id: int,
        vehicle_name: str,
        vehicle_info: dict,
    ) -> None:
        super().__init__(
            coordinator,
            vehicle_id,
            vehicle_name,
            vehicle_info,
            key="latest_gas",
            sensor_name="Latest Fuel Fill",
            unique_id_suffix="latest_gas",
            device_class=SensorDeviceClass.TIMESTAMP,
        )

    @property
    def native_value(self) -> datetime | None:
        rec = self._record
        if not rec:
            return None

        for field in ("date", "Date", "FuelDate"):
            dt = parse_date(rec.get(field))
            if dt:
                return dt
        return None

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        return self._record or None


class LubeLoggerNextReminderSensor(BaseLubeLoggerSensor):
    """Sensor for next reminder."""

    def __init__(
        self,
        coordinator: LubeLoggerDataUpdateCoordinator,
        vehicle_id: int,
        vehicle_name: str,
        vehicle_info: dict,
    ) -> None:
        super().__init__(
            coordinator,
            vehicle_id,
            vehicle_name,
            vehicle_info,
            key="next_reminder",
            sensor_name="Next Reminder",
            unique_id_suffix="next_reminder",
            device_class=SensorDeviceClass.TIMESTAMP,
        )

    @property
    def native_value(self) -> datetime | None:
        rec = self._record
        if not rec:
            return None

        # API uses dueDate for reminders
        for field in ("dueDate", "DueDate", "Date", "date"):
            dt = parse_date(rec.get(field))
            if dt:
                return dt
        return None

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        return self._record or None
