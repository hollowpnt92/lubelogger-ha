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

    # US and EU date e time format
    formats = [
        "%d/%m/%Y",           # EU format: "28/02/2027"
        "%d/%m/%Y %H:%M:%S",  # EU format with time
        "%m/%d/%Y",           # US format (fallback)
        "%m/%d/%Y %H:%M:%S",  # US format with time (fallback)
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


def convert_european_number(number_str: Any) -> float | int | str:
    """Convert European number format (1.234,56) to Python float/int."""
    if not number_str:
        return None
    
    if isinstance(number_str, (int, float)):
        return number_str
    
    if isinstance(number_str, str):
       
        number_str = number_str.replace('€', '').replace('$', '').replace('£', '').strip()
        
        # "European format: dot as thousands separator, comma as decimal separator."
        if ',' in number_str and '.' in number_str:
            # Format: 1.234,56 → remove dots, replace comma
            number_str = number_str.replace('.', '').replace(',', '.')
        elif ',' in number_str:
            # Format: 1234,56 → replace comma
            number_str = number_str.replace(',', '.')
        # If there are only dots, they could be US decimals or EU thousands.
        elif '.' in number_str and len(number_str.split('.')[-1]) == 3:
            # Likely format: 1.234 → remove dot
            number_str = number_str.replace('.', '')
        
        try:
            # Try as float
            result = float(number_str)
            # If it's an integer without decimals, return int
            if result.is_integer():
                return int(result)
            return result
        except (ValueError, TypeError):
            return number_str
    
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
            return convert_european_number(odometer)
        return None

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        attrs = self._record.copy() if self._record else {}
        
        # Add the date in a readable format
        if attrs and "date" in attrs:
            try:
                dt = parse_date(attrs["date"])
                if dt:
                    attrs["data_formatted"] = dt.strftime("%d/%m/%Y")
            except (ValueError, TypeError):
                pass
        
        return attrs or None


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

        for field in ("dateCreated", "dateModified", "Date", "date"):
            dt = parse_date(rec.get(field))
            if dt:
                return dt
        return None

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        attrs = self._record.copy() if self._record else {}
        
        # Convert any numbers in European format
        if attrs and "cost" in attrs:
            attrs["cost"] = convert_european_number(attrs["cost"])
        
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
        
        return attrs or None


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
            unit="EUR",
        )

    @property
    def native_value(self) -> Any:
        rec = self._record
        if not rec:
            return None
        
        cost = rec.get("cost") or rec.get("Cost")
        if cost:
            return convert_european_number(cost)
        return None

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        attrs = self._record.copy() if self._record else {}
        
        # Aggiungi la data in formato leggibile
        date_fields = ["date", "Date", "taxDate"]
        for field in date_fields:
            if field in attrs:
                try:
                    dt = parse_date(attrs[field])
                    if dt:
                        attrs["data_formattata"] = dt.strftime("%d/%m/%Y")
                except (ValueError, TypeError):
                    pass
                break
        
        return attrs or None


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
            sensor_name="Ultimo Servizio",
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
        attrs = self._record.copy() if self._record else {}
        
        # Converti eventuali costi nel formato europeo
        cost_fields = ["cost", "Cost", "totalCost", "laborCost", "partsCost"]
        for field in cost_fields:
            if field in attrs:
                attrs[field] = convert_european_number(attrs[field])
        
        # Aggiungi la data in formato leggibile
        date_fields = ["date", "Date", "ServiceDate"]
        for field in date_fields:
            if field in attrs:
                try:
                    dt = parse_date(attrs[field])
                    if dt:
                        attrs["data_formattata"] = dt.strftime("%d/%m/%Y")
                except (ValueError, TypeError):
                    pass
                break
        
        return attrs or None


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
            sensor_name="Ultima Riparazione",
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
        attrs = self._record.copy() if self._record else {}
        
        # Converti eventuali costi nel formato europeo
        cost_fields = ["cost", "Cost", "totalCost", "laborCost", "partsCost"]
        for field in cost_fields:
            if field in attrs:
                attrs[field] = convert_european_number(attrs[field])
        
        # Aggiungi la data in formato leggibile
        date_fields = ["date", "Date", "RepairDate"]
        for field in date_fields:
            if field in attrs:
                try:
                    dt = parse_date(attrs[field])
                    if dt:
                        attrs["data_formattata"] = dt.strftime("%d/%m/%Y")
                except (ValueError, TypeError):
                    pass
                break
        
        return attrs or None


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
            sensor_name="Ultimo Upgrade",
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
        attrs = self._record.copy() if self._record else {}
        
        # Converti eventuali costi nel formato europeo
        cost_fields = ["cost", "Cost", "totalCost"]
        for field in cost_fields:
            if field in attrs:
                attrs[field] = convert_european_number(attrs[field])
        
        # Aggiungi la data in formato leggibile
        date_fields = ["date", "Date", "UpgradeDate"]
        for field in date_fields:
            if field in attrs:
                try:
                    dt = parse_date(attrs[field])
                    if dt:
                        attrs["data_formattata"] = dt.strftime("%d/%m/%Y")
                except (ValueError, TypeError):
                    pass
                break
        
        return attrs or None


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
            sensor_name="Ultima Fornitura",
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
        attrs = self._record.copy() if self._record else {}
        
        # Converti eventuali costi nel formato europeo
        cost_fields = ["cost", "Cost", "totalCost", "price"]
        for field in cost_fields:
            if field in attrs:
                attrs[field] = convert_european_number(attrs[field])
        
        # Aggiungi la data in formato leggibile
        date_fields = ["date", "Date", "SupplyDate"]
        for field in date_fields:
            if field in attrs:
                try:
                    dt = parse_date(attrs[field])
                    if dt:
                        attrs["data_formattata"] = dt.strftime("%d/%m/%Y")
                except (ValueError, TypeError):
                    pass
                break
        
        return attrs or None


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
            sensor_name="Ultimo Rifornimento",
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
        attrs = self._record.copy() if self._record else {}
        
        # Converti tutti i numeri nel formato europeo
        numeric_fields = ["cost", "Cost", "price", "quantity", "odometer", "totalCost", "fuelConsumed"]
        for field in numeric_fields:
            if field in attrs:
                attrs[field] = convert_european_number(attrs[field])
        
        # GESTIONE CONSUMI - CONVERSIONE ESPLICITA per fuelEconomy
        if "fuelEconomy" in attrs:
            fuel_value = attrs["fuelEconomy"]
            
            # Se è una stringa con virgola, converti in float
            if isinstance(fuel_value, str):
                fuel_value = fuel_value.replace(',', '.')
                try:
                    fuel_value = float(fuel_value)
                except (ValueError, TypeError):
                    pass
            
            # Se è un numero, converti in km/l e arrotonda
            if isinstance(fuel_value, (int, float)) and fuel_value > 0:
                # Conversione l/100km → km/l (100 / consumo)
                # Consumo tipico: 5.46 l/100km → 100/5.46 ≈ 18.32 km/l
                fuel_value = 100 / fuel_value
                fuel_value = round(fuel_value, 2)  # Arrotonda a 2 decimali
            
            attrs["fuelEconomy"] = fuel_value
            attrs["fuelEconomy_unit"] = "km/l"
        
        # Gestione altri campi consumo simili
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
                    if raw_value < 20:  # Probabilmente l/100km
                        raw_value = 100 / raw_value
                    raw_value = round(raw_value, 2)
                
                attrs[field] = raw_value
                attrs[f"{field}_unit"] = "km/l"
        
        # Aggiungi la data in formato leggibile
        date_fields = ["date", "Date", "FuelDate"]
        for field in date_fields:
            if field in attrs:
                try:
                    dt = parse_date(attrs[field])
                    if dt:
                        attrs["data_formattata"] = dt.strftime("%d/%m/%Y")
                except (ValueError, TypeError):
                    pass
                break
        
        return attrs or None


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
            sensor_name="Prossimo Promemoria",
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
        attrs = self._record.copy() if self._record else {}
        
        # Converti distanze in formato europeo
        distance_fields = ["dueDistance", "dueOdometer", "distance"]
        for field in distance_fields:
            if field in attrs:
                attrs[field] = convert_european_number(attrs[field])
        
        # Aggiungi la data di scadenza in formato leggibile
        if "dueDate" in attrs:
            try:
                dt = parse_date(attrs["dueDate"])
                if dt:
                    attrs["data_scadenza_formattata"] = dt.strftime("%d/%m/%Y")
            except (ValueError, TypeError):
                pass
        
        # Calcola lo stato reale della scadenza
        due_distance = attrs.get("dueDistance")
        due_days = attrs.get("dueDays")
        metric = attrs.get("metric", "")
        urgency = attrs.get("urgency", "")
        
        # Determina se è scaduto
        is_overdue = False
        overdue_by = None
        
        if urgency == "PastDue":
            is_overdue = True
        elif due_distance is not None and due_distance < 0:
            is_overdue = True
            overdue_by = f"{-due_distance} km"
        elif due_days is not None and due_days < 0:
            is_overdue = True
            overdue_by = f"{-due_days} giorni"
        
        attrs["scaduto"] = is_overdue
        if overdue_by:
            attrs["scaduto_da"] = overdue_by
        
        # Aggiungi info sulla metrica
        if "Odometer" in metric:
            attrs["tipo_promemoria"] = "Chilometrico"
            if due_distance is not None:
                if due_distance < 0:
                    attrs["stato"] = f"Scaduto da {-due_distance} km"
                else:
                    attrs["stato"] = f"Tra {due_distance} km"
        elif "Date" in metric:
            attrs["tipo_promemoria"] = "Temporale"
            if due_days is not None:
                if due_days < 0:
                    attrs["stato"] = f"Scaduto da {-due_days} giorni"
                else:
                    attrs["stato"] = f"Tra {due_days} giorni"
        else:
            attrs["tipo_promemoria"] = "Misto"
        
        return attrs or None
