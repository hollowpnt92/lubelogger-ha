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

    # US and EU date and time format
    formats = [
        "%d/%m/%Y",           # EU format: "28/02/2027"
        "%d/%m/%Y %H:%M:%S",  # EU format with time
        "%m/%d/%Y",           # US format (fallback)
        "%m/%d/%Y %H:%M:%S",  # US format with time (fallback)
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-dT%H:%M:%S.%f",
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


def convert_number_string(number_str: Any) -> float | int | str | None:
    """Convert a number string to a number, handling both European and International formats.
    
    European format: 1.234,56 -> 1234.56
    International format: 1,234.56 -> 1234.56
    """
    if number_str is None or number_str == "":
        return None
    
    if isinstance(number_str, (int, float)):
        return number_str
    
    if isinstance(number_str, str):
        original = number_str
        # Remove common currency symbols and trim
        number_str = number_str.replace('€', '').replace('$', '').replace('£', '').strip()
        
        # Helper to check if a part is likely a thousands group (exactly 3 digits)
        def is_thousands_part(part: str) -> bool:
            return part.isdigit() and len(part) == 3
        
        # Count separators
        comma_count = number_str.count(',')
        dot_count = number_str.count('.')
        
        # Case 1: Only one type of separator
        if comma_count == 1 and dot_count == 0:
            # e.g., "1234,56" or "1,234"
            parts = number_str.split(',')
            if len(parts) == 2 and not is_thousands_part(parts[1]):
                # Single comma with non-3-digit right part -> decimal comma
                number_str = number_str.replace(',', '.')
            else:
                # Could be a thousands comma (e.g., "1,234") -> remove it
                number_str = number_str.replace(',', '')
        
        elif dot_count == 1 and comma_count == 0:
            # e.g., "1234.56" or "1.234"
            parts = number_str.split('.')
            if len(parts) == 2 and not is_thousands_part(parts[1]):
                # Single dot with non-3-digit right part -> decimal dot, keep as is
                pass
            else:
                # Likely a thousands dot (e.g., "1.234") -> remove it
                number_str = number_str.replace('.', '')
        
        # Case 2: Both separators present (e.g., "1.234,56" or "1,234.56")
        elif comma_count > 0 and dot_count > 0:
            last_comma = number_str.rfind(',')
            last_dot = number_str.rfind('.')
            
            # Assume the LAST separator is the decimal point
            if last_comma > last_dot:
                # European: last separator is comma -> dot is thousands
                number_str = number_str.replace('.', '').replace(',', '.')
            else:
                # International: last separator is dot -> comma is thousands
                number_str = number_str.replace(',', '')
                # Dot remains as decimal
        
        # Case 3: Multiple separators of the same type (thousands)
        elif comma_count > 1:
            # e.g., "1,234,567"
            number_str = number_str.replace(',', '')
        elif dot_count > 1:
            # e.g., "1.234.567"
            number_str = number_str.replace('.', '')
        
        # Final conversion
        try:
            result = float(number_str)
            return int(result) if result.is_integer() else result
        except (ValueError, TypeError):
            # If conversion fails, return the cleaned original string
            return original.strip()
    
    return number_str


def convert_fuel_consumption(value: Any) -> float | str:
    """Convert fuel consumption from l/100km to km/l with 2 decimals."""
    if value is None or value == "":
        return None
    
    # If it's already a number
    if isinstance(value, (int, float)):
        num_value = float(value)
    # If it's a string, convert European format
    elif isinstance(value, str):
        # Replace comma with dot for European format
        value_clean = value.replace(',', '.')
        try:
            num_value = float(value_clean)
        except (ValueError, TypeError):
            # If it cannot be converted, return the original string
            return value
    else:
        return value
    
    # Conversion l/100km → km/l
    # Realistic consumption: l/100km are typically between 3 and 20
    # km/l are typically between 5 and 33
    if 2 < num_value < 30:  # Likely l/100km
        num_value = 100 / num_value
    
    # Round to 2 decimal places
    return round(num_value, 2)


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

    # This tells HA to generate the entity name using the device name + translation
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: LubeLoggerDataUpdateCoordinator,
        vehicle_id: int,
        vehicle_name: str,
        vehicle_info: dict,
        key: str,
        translation_key: str,
        unique_id_suffix: str,
        device_class: SensorDeviceClass | None = None,
        state_class: SensorStateClass | None = None,
        unit: str | None = None,
    ) -> None:
        super().__init__(coordinator)
        self._vehicle_id = vehicle_id
        self._vehicle_name = vehicle_name
        self._key = key
        self._attr_translation_key = translation_key
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
            coordinator=coordinator,
            vehicle_id=vehicle_id,
            vehicle_name=vehicle_name,
            vehicle_info=vehicle_info,
            key="latest_odometer",
            translation_key="latest_odometer",
            unique_id_suffix="latest_odometer",
            device_class=SensorDeviceClass.DISTANCE,
            state_class=SensorStateClass.MEASUREMENT,
            unit="km",
        )

    @property
    def native_value(self) -> Any:
        rec = self._record
        if not rec:
            return None
        
        if rec.get("adjusted"):
            odometer = rec.get("odometer")
        else:
            odometer = rec.get("odometer") or rec.get("Odometer")
        
        if odometer:
            return convert_number_string(odometer)
        return None

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        if not self._record:
            return None
        
        attrs = {}
        # Process ALL fields in the record to make them interoperable
        for key, value in self._record.items():
            # Convert any value that looks like a number
            if isinstance(value, str) and any(char.isdigit() for char in value):
                attrs[key] = convert_number_string(value)
            else:
                attrs[key] = value
        
        # Add the date in a readable format
        if "date" in attrs:
            try:
                dt = parse_date(attrs["date"])
                if dt:
                    attrs["date_formatted"] = dt.strftime("%d/%m/%Y")
            except (ValueError, TypeError):
                pass
        
        return attrs


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
            coordinator=coordinator,
            vehicle_id=vehicle_id,
            vehicle_name=vehicle_name,
            vehicle_info=vehicle_info,
            key="next_plan",
            translation_key="next_plan",
            unique_id_suffix="next_plan",
            device_class=SensorDeviceClass.TIMESTAMP,
        )

    @property
    def native_value(self) -> datetime | None:
        rec = self._record
        if not rec:
            return None

        for field in ("dateCreated", "dateModified", "Date", "date"):
            dt = parse_date(rec.get(field))
            if dt:
                return dt
        return None

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        if not self._record:
            return None
        
        attrs = {}
        # Process ALL fields in the record to make them interoperable
        for key, value in self._record.items():
            # Convert any value that looks like a number
            if isinstance(value, str) and any(char.isdigit() for char in value):
                attrs[key] = convert_number_string(value)
            else:
                attrs[key] = value
        
        # Add the date in a readable format
        date_fields = ["dateCreated", "dateModified", "Date", "date"]
        for field in date_fields:
            if field in attrs:
                try:
                    dt = parse_date(attrs[field])
                    if dt:
                        attrs[f"{field}_formatted"] = dt.strftime("%d/%m/%Y")
                except (ValueError, TypeError):
                    pass
                break
        
        return attrs


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
            coordinator=coordinator,
            vehicle_id=vehicle_id,
            vehicle_name=vehicle_name,
            vehicle_info=vehicle_info,
            key="latest_tax",
            translation_key="latest_tax",
            unique_id_suffix="latest_tax",
            device_class=SensorDeviceClass.MONETARY,
            state_class=None,
            unit="EUR",
        )

    @property
    def native_value(self) -> Any:
        rec = self._record
        if not rec:
            return None
        
        cost = rec.get("cost") or rec.get("Cost")
        if cost:
            return convert_number_string(cost)
        return None

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        if not self._record:
            return None
        
        attrs = {}
        # Process ALL fields in the record to make them interoperable
        for key, value in self._record.items():
            # Convert any value that looks like a number
            if isinstance(value, str) and any(char.isdigit() for char in value):
                attrs[key] = convert_number_string(value)
            else:
                attrs[key] = value
        
        # Add date in readable format
        date_fields = ["date", "Date", "taxDate"]
        for field in date_fields:
            if field in attrs:
                try:
                    dt = parse_date(attrs[field])
                    if dt:
                        attrs["date_formatted"] = dt.strftime("%d/%m/%Y")
                except (ValueError, TypeError):
                    pass
                break
        
        return attrs


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
            coordinator=coordinator,
            vehicle_id=vehicle_id,
            vehicle_name=vehicle_name,
            vehicle_info=vehicle_info,
            key="latest_service",
            translation_key="latest_service",
            unique_id_suffix="latest_service",
            device_class=SensorDeviceClass.TIMESTAMP,
        )

    @property
    def native_value(self) -> datetime | None:
        rec = self._record
        if not rec:
            return None

        for field in ("date", "Date", "ServiceDate"):
            dt = parse_date(rec.get(field))
            if dt:
                return dt
        return None

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        if not self._record:
            return None
        
        attrs = {}
        # Process ALL fields in the record to make them interoperable
        for key, value in self._record.items():
            # Convert any value that looks like a number
            if isinstance(value, str) and any(char.isdigit() for char in value):
                attrs[key] = convert_number_string(value)
            else:
                attrs[key] = value
        
        # Add date in readable format
        date_fields = ["date", "Date", "ServiceDate"]
        for field in date_fields:
            if field in attrs:
                try:
                    dt = parse_date(attrs[field])
                    if dt:
                        attrs["date_formatted"] = dt.strftime("%d/%m/%Y")
                except (ValueError, TypeError):
                    pass
                break
        
        return attrs


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
            coordinator=coordinator,
            vehicle_id=vehicle_id,
            vehicle_name=vehicle_name,
            vehicle_info=vehicle_info,
            key="latest_repair",
            translation_key="latest_repair",
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
        if not self._record:
            return None
        
        attrs = {}
        # Process ALL fields in the record to make them interoperable
        for key, value in self._record.items():
            # Convert any value that looks like a number
            if isinstance(value, str) and any(char.isdigit() for char in value):
                attrs[key] = convert_number_string(value)
            else:
                attrs[key] = value
        
        # Add date in readable format
        date_fields = ["date", "Date", "RepairDate"]
        for field in date_fields:
            if field in attrs:
                try:
                    dt = parse_date(attrs[field])
                    if dt:
                        attrs["date_formatted"] = dt.strftime("%d/%m/%Y")
                except (ValueError, TypeError):
                    pass
                break
        
        return attrs


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
            coordinator=coordinator,
            vehicle_id=vehicle_id,
            vehicle_name=vehicle_name,
            vehicle_info=vehicle_info,
            key="latest_upgrade",
            translation_key="latest_upgrade",
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
        if not self._record:
            return None
        
        attrs = {}
        # Process ALL fields in the record to make them interoperable
        for key, value in self._record.items():
            # Convert any value that looks like a number
            if isinstance(value, str) and any(char.isdigit() for char in value):
                attrs[key] = convert_number_string(value)
            else:
                attrs[key] = value
        
        # Add date in readable format
        date_fields = ["date", "Date", "UpgradeDate"]
        for field in date_fields:
            if field in attrs:
                try:
                    dt = parse_date(attrs[field])
                    if dt:
                        attrs["date_formatted"] = dt.strftime("%d/%m/%Y")
                except (ValueError, TypeError):
                    pass
                break
        
        return attrs


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
            coordinator=coordinator,
            vehicle_id=vehicle_id,
            vehicle_name=vehicle_name,
            vehicle_info=vehicle_info,
            key="latest_supply",
            translation_key="latest_supply",
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
        if not self._record:
            return None
        
        attrs = {}
        # Process ALL fields in the record to make them interoperable
        for key, value in self._record.items():
            # Convert any value that looks like a number
            if isinstance(value, str) and any(char.isdigit() for char in value):
                attrs[key] = convert_number_string(value)
            else:
                attrs[key] = value
        
        # Add date in readable format
        date_fields = ["date", "Date", "SupplyDate"]
        for field in date_fields:
            if field in attrs:
                try:
                    dt = parse_date(attrs[field])
                    if dt:
                        attrs["date_formatted"] = dt.strftime("%d/%m/%Y")
                except (ValueError, TypeError):
                    pass
                break
        
        return attrs


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
            coordinator=coordinator,
            vehicle_id=vehicle_id,
            vehicle_name=vehicle_name,
            vehicle_info=vehicle_info,
            key="latest_gas",
            translation_key="latest_gas",
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
        if not self._record:
            return None
        
        attrs = {}
        # Process ALL fields in the record to make them interoperable
        for key, value in self._record.items():
            # Convert any value that looks like a number
            if isinstance(value, str) and any(char.isdigit() for char in value):
                attrs[key] = convert_number_string(value)
            else:
                attrs[key] = value
        
        # FUEL CONSUMPTION - EXPLICIT CONVERSION for fuelEconomy
        if "fuelEconomy" in attrs:
            fuel_value = attrs["fuelEconomy"]
            
            # If it's a string with comma, convert to float
            if isinstance(fuel_value, str):
                fuel_value = fuel_value.replace(',', '.')
                try:
                    fuel_value = float(fuel_value)
                except (ValueError, TypeError):
                    pass
            
            # If it's a number, convert to km/l and round
            if isinstance(fuel_value, (int, float)) and fuel_value > 0:
                # Conversion l/100km → km/l (100 / consumption)
                fuel_value = 100 / fuel_value
                fuel_value = round(fuel_value, 2)  # Round to 2 decimals
            
            attrs["fuelEconomy"] = fuel_value
            attrs["fuelEconomy_unit"] = "km/l"
        
        # Handle other similar consumption fields
        other_consumption_fields = ["consumption", "litersPer100km", "averageConsumption"]
        for field in other_consumption_fields:
            if field in attrs:
                raw_value = attrs[field]
                if isinstance(raw_value, str):
                    raw_value = raw_value.replace(',', '.')
                    try:
                        raw_value = float(raw_value)
                    except (ValueError, TypeError):
                        pass
                
                if isinstance(raw_value, (int, float)) and raw_value > 0:
                    if raw_value < 20:  # Probably l/100km
                        raw_value = 100 / raw_value
                    raw_value = round(raw_value, 2)
                
                attrs[field] = raw_value
                attrs[f"{field}_unit"] = "km/l"
        
        # Add date in readable format
        date_fields = ["date", "Date", "FuelDate"]
        for field in date_fields:
            if field in attrs:
                try:
                    dt = parse_date(attrs[field])
                    if dt:
                        attrs["date_formatted"] = dt.strftime("%d/%m/%Y")
                except (ValueError, TypeError):
                    pass
                break
        
        return attrs


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
            coordinator=coordinator,
            vehicle_id=vehicle_id,
            vehicle_name=vehicle_name,
            vehicle_info=vehicle_info,
            key="next_reminder",
            translation_key="next_reminder",
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
        if not self._record:
            return None
        
        attrs = {}
        # Process ALL fields in the record to make them interoperable
        for key, value in self._record.items():
            # Convert any value that looks like a number
            if isinstance(value, str) and any(char.isdigit() for char in value):
                attrs[key] = convert_number_string(value)
            else:
                attrs[key] = value
        
        # Add due date in readable format
        if "dueDate" in attrs:
            try:
                dt = parse_date(attrs["dueDate"])
                if dt:
                    attrs["due_date_formatted"] = dt.strftime("%d/%m/%Y")
            except (ValueError, TypeError):
                pass
        
        # Calculate the actual status of the reminder
        due_distance = attrs.get("dueDistance")
        due_days = attrs.get("dueDays")
        metric = attrs.get("metric", "")
        urgency = attrs.get("urgency", "")
        
        # Determine if it's overdue
        is_overdue = False
        overdue_by = None
        
        if urgency == "PastDue":
            is_overdue = True
        elif due_distance is not None and due_distance < 0:
            is_overdue = True
            overdue_by = f"{-due_distance} km"
        elif due_days is not None and due_days < 0:
            is_overdue = True
            overdue_by = f"{-due_days} days"
        
        attrs["overdue"] = is_overdue
        if overdue_by:
            attrs["overdue_by"] = overdue_by
        
        # Add info about the metric
        if "Odometer" in metric:
            attrs["reminder_type"] = "By distance"
            if due_distance is not None:
                if due_distance < 0:
                    attrs["status"] = f"Overdue by {-due_distance} km"
                else:
                    attrs["status"] = f"In {due_distance} km"
        elif "Date" in metric:
            attrs["reminder_type"] = "By time"
            if due_days is not None:
                if due_days < 0:
                    attrs["status"] = f"Overdue by {-due_days} days"
                else:
                    attrs["status"] = f"In {due_days} days"
        else:
            attrs["reminder_type"] = "Mixed"
        
        return attrs