"""Client for interacting with LubeLogger API."""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

import aiohttp
from homeassistant.util import dt as dt_util

from .const import (
    API_ROOT,  # Added back as requested
    API_ADJUSTED_ODOMETER,
    API_GAS_RECORD,
    API_ODOMETER,
    API_PLAN,
    API_REMINDER,
    API_REPAIR_RECORD,
    API_SERVICE_RECORD,
    API_SUPPLY_RECORD,
    API_TAX,
    API_UPGRADE_RECORD,
    API_VEHICLES,
)

_LOGGER = logging.getLogger(__name__)


def parse_date_string(date_str: str) -> datetime | None:
    """Parse a date string in multiple formats and return timezone-aware datetime.
    
    Tries European formats (DD/MM/YYYY) first, then US formats.
    All returned datetime objects are timezone-aware (required by Home Assistant).
    """
    if not date_str:
        return None

    # Try ISO format first (handles timezone-aware strings)
    try:
        if date_str.endswith("Z"):
            date_str = date_str.replace("Z", "+00:00")
        dt = datetime.fromisoformat(date_str)
        # Ensure timezone-aware - use UTC if no timezone info
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=dt_util.UTC)
        return dt
    except (ValueError, AttributeError):
        pass

    # European formats first, then US formats
    formats = [
        "%d/%m/%Y",           # European format: "28/02/2027"
        "%d/%m/%Y %H:%M:%S",  # European with time
        "%m/%d/%Y",           # US format: "12/17/2025"
        "%m/%d/%Y %H:%M:%S",  # US with time
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%dT%H:%M:%S.%f",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d",
    ]

    for fmt in formats:
        try:
            dt = datetime.strptime(date_str, fmt)
            # Make timezone-aware (assume local timezone, then convert to UTC)
            if dt.tzinfo is None:
                dt = dt_util.as_local(dt)
            return dt
        except (ValueError, AttributeError):
            continue

    return None


def get_reminder_priority(reminder: dict[str, Any]) -> tuple:
    """Calculate priority for reminder sorting.
    
    Returns a tuple for sorting:
    (is_overdue, distance_priority, date_priority, description)
    
    Lower values = higher priority.
    """
    # Priority 1: PastDue urgency
    is_past_due = reminder.get("urgency") == "PastDue"
    
    # Priority 2: Negative distances (overdue by km)
    due_distance = reminder.get("dueDistance")
    try:
        distance = float(due_distance) if due_distance not in [None, ""] else 0
    except (ValueError, TypeError):
        distance = 0
    
    # Priority 3: Negative days (overdue by time)
    due_days = reminder.get("dueDays")
    try:
        days = int(due_days) if due_days not in [None, ""] else 0
    except (ValueError, TypeError):
        days = 0
    
    # Create priority tuple:
    # 1. Non-overdue first (False < True in sorting, so we invert)
    # 2. Most negative distance first (smaller = higher priority)
    # 3. Most negative days first (smaller = higher priority)
    # 4. Alphabetical description as tiebreaker
    
    # Invert is_past_due so False (not past due) sorts before True (past due)
    overdue_priority = not is_past_due
    
    # For distance: negative values (overdue) should come first
    # More negative = smaller number = higher priority
    distance_priority = -distance if distance < 0 else float('inf')
    
    # For days: same logic
    days_priority = -days if days < 0 else float('inf')
    
    description = reminder.get("description", "")
    
    return (overdue_priority, distance_priority, days_priority, description)


class LubeLoggerClient:
    """Client for LubeLogger API."""

    def __init__(
        self,
        url: str,
        username: str,
        password: str,
        session: aiohttp.ClientSession | None = None,
    ) -> None:
        """Initialize the client."""
        self._url = url.rstrip("/")
        self._username = username
        self._password = password
        self._session = session
        self._auth = aiohttp.BasicAuth(username, password)

    async def async_get_vehicles(self) -> list[dict[str, Any]]:
        """Get all vehicles from LubeLogger."""
        vehicles = await self._async_request(API_VEHICLES)
        if not isinstance(vehicles, list):
            return []
        return vehicles

    async def async_get_latest_odometer(
        self, vehicle_id: int | None = None
    ) -> dict[str, Any] | None:
        """Get the latest odometer record for a vehicle."""
        if vehicle_id:
            try:
                endpoint = f"{API_ADJUSTED_ODOMETER}?vehicleId={vehicle_id}"
                adjusted = await self._async_request(endpoint)
                if adjusted and isinstance(adjusted, dict):
                    _LOGGER.debug("Using adjusted odometer for vehicle %s: %s", vehicle_id, adjusted)
                    return {"odometer": adjusted, "adjusted": True}
            except Exception as err:
                _LOGGER.debug("Adjusted odometer not available for vehicle %s: %s", vehicle_id, err)
        
        endpoint = f"{API_ODOMETER}?vehicleId={vehicle_id}" if vehicle_id else API_ODOMETER
        records = await self._async_request(endpoint)
        if not isinstance(records, list) or not records:
            _LOGGER.debug("No odometer records found for vehicle %s", vehicle_id)
            return None

        def sort_key(rec: dict[str, Any]) -> Any:
            rec_id = rec.get("id") or rec.get("Id")
            if rec_id:
                try:
                    return int(rec_id)
                except (ValueError, TypeError):
                    return rec_id
            return 0

        latest = sorted(records, key=sort_key)[-1]
        _LOGGER.debug("Latest odometer for vehicle %s: %s", vehicle_id, latest)
        return latest

    async def async_get_next_plan(
        self, vehicle_id: int | None = None
    ) -> dict[str, Any] | None:
        """Get the next upcoming plan item for a vehicle."""
        endpoint = f"{API_PLAN}?vehicleId={vehicle_id}" if vehicle_id else API_PLAN
        records = await self._async_request(endpoint)
        if not isinstance(records, list) or not records:
            _LOGGER.debug("No plan records found for vehicle %s", vehicle_id)
            return None
        
        def sort_key(rec: dict[str, Any]) -> Any:
            date_str = rec.get("dateCreated") or rec.get("dateModified") or rec.get("Date") or rec.get("date")
            if date_str:
                dt = parse_date_string(date_str)
                if dt:
                    return dt
            return datetime.max
        
        sorted_records = sorted([r for r in records if sort_key(r) != datetime.max], key=sort_key)
        if sorted_records:
            _LOGGER.debug("Next plan for vehicle %s: %s", vehicle_id, sorted_records[0])
            return sorted_records[0]
        return None

    async def async_get_latest_tax(
        self, vehicle_id: int | None = None
    ) -> dict[str, Any] | None:
        """Get the latest tax record for a vehicle."""
        endpoint = f"{API_TAX}?vehicleId={vehicle_id}" if vehicle_id else API_TAX
        records = await self._async_request(endpoint)
        if not isinstance(records, list) or not records:
            _LOGGER.debug("No tax records found for vehicle %s", vehicle_id)
            return None

        def sort_key(rec: dict[str, Any]) -> Any:
            rec_id = rec.get("id") or rec.get("Id")
            if rec_id:
                try:
                    return int(rec_id)
                except (ValueError, TypeError):
                    return rec_id
            return 0

        latest = sorted(records, key=sort_key)[-1]
        _LOGGER.debug("Latest tax for vehicle %s: %s", vehicle_id, latest)
        return latest

    async def async_get_latest_service(
        self, vehicle_id: int | None = None
    ) -> dict[str, Any] | None:
        """Get the latest service record for a vehicle."""
        endpoint = f"{API_SERVICE_RECORD}?vehicleId={vehicle_id}" if vehicle_id else API_SERVICE_RECORD
        records = await self._async_request(endpoint)
        if not isinstance(records, list) or not records:
            _LOGGER.debug("No service records found for vehicle %s", vehicle_id)
            return None

        def sort_key(rec: dict[str, Any]) -> Any:
            rec_id = rec.get("id") or rec.get("Id")
            if rec_id:
                try:
                    return int(rec_id)
                except (ValueError, TypeError):
                    return rec_id
            return 0

        latest = sorted(records, key=sort_key)[-1]
        _LOGGER.debug("Latest service for vehicle %s: %s", vehicle_id, latest)
        return latest

    async def async_get_latest_repair(
        self, vehicle_id: int | None = None
    ) -> dict[str, Any] | None:
        """Get the latest repair record for a vehicle."""
        endpoint = f"{API_REPAIR_RECORD}?vehicleId={vehicle_id}" if vehicle_id else API_REPAIR_RECORD
        records = await self._async_request(endpoint)
        if not isinstance(records, list) or not records:
            _LOGGER.debug("No repair records found for vehicle %s", vehicle_id)
            return None

        def sort_key(rec: dict[str, Any]) -> Any:
            rec_id = rec.get("id") or rec.get("Id")
            if rec_id:
                try:
                    return int(rec_id)
                except (ValueError, TypeError):
                    return rec_id
            return 0

        latest = sorted(records, key=sort_key)[-1]
        _LOGGER.debug("Latest repair for vehicle %s: %s", vehicle_id, latest)
        return latest

    async def async_get_latest_upgrade(
        self, vehicle_id: int | None = None
    ) -> dict[str, Any] | None:
        """Get the latest upgrade record for a vehicle."""
        endpoint = f"{API_UPGRADE_RECORD}?vehicleId={vehicle_id}" if vehicle_id else API_UPGRADE_RECORD
        records = await self._async_request(endpoint)
        if not isinstance(records, list) or not records:
            _LOGGER.debug("No upgrade records found for vehicle %s", vehicle_id)
            return None

        def sort_key(rec: dict[str, Any]) -> Any:
            rec_id = rec.get("id") or rec.get("Id")
            if rec_id:
                try:
                    return int(rec_id)
                except (ValueError, TypeError):
                    return rec_id
            return 0

        latest = sorted(records, key=sort_key)[-1]
        _LOGGER.debug("Latest upgrade for vehicle %s: %s", vehicle_id, latest)
        return latest

    async def async_get_latest_supply(
        self, vehicle_id: int | None = None
    ) -> dict[str, Any] | None:
        """Get the latest supply record for a vehicle."""
        endpoint = f"{API_SUPPLY_RECORD}?vehicleId={vehicle_id}" if vehicle_id else API_SUPPLY_RECORD
        records = await self._async_request(endpoint)
        if not isinstance(records, list) or not records:
            _LOGGER.debug("No supply records found for vehicle %s", vehicle_id)
            return None

        def sort_key(rec: dict[str, Any]) -> Any:
            rec_id = rec.get("id") or rec.get("Id")
            if rec_id:
                try:
                    return int(rec_id)
                except (ValueError, TypeError):
                    return rec_id
            return 0

        latest = sorted(records, key=sort_key)[-1]
        _LOGGER.debug("Latest supply for vehicle %s: %s", vehicle_id, latest)
        return latest

    async def async_get_latest_gas(
        self, vehicle_id: int | None = None
    ) -> dict[str, Any] | None:
        """Get the latest gas/fuel record for a vehicle."""
        endpoint = f"{API_GAS_RECORD}?vehicleId={vehicle_id}" if vehicle_id else API_GAS_RECORD
        records = await self._async_request(endpoint)
        if not isinstance(records, list) or not records:
            _LOGGER.debug("No gas records found for vehicle %s", vehicle_id)
            return None

        def sort_key(rec: dict[str, Any]) -> Any:
            rec_id = rec.get("id") or rec.get("Id")
            if rec_id:
                try:
                    return int(rec_id)
                except (ValueError, TypeError):
                    return rec_id
            return 0

        latest = sorted(records, key=sort_key)[-1]
        _LOGGER.debug("Latest gas for vehicle %s: %s", vehicle_id, latest)
        return latest

    async def async_get_next_reminder(
        self, vehicle_id: int | None = None
    ) -> dict[str, Any] | None:
        """Get the next upcoming reminder for a vehicle."""
        endpoint = f"{API_REMINDER}?vehicleId={vehicle_id}" if vehicle_id else API_REMINDER
        records = await self._async_request(endpoint)
        if not isinstance(records, list) or not records:
            _LOGGER.debug("No reminders found for vehicle %s", vehicle_id)
            return None

        # Sort reminders by priority (overdue ones first)
        sorted_records = sorted(records, key=get_reminder_priority)
        
        if sorted_records:
            next_reminder = sorted_records[0]
            _LOGGER.debug("Next reminder for vehicle %s: %s", vehicle_id, next_reminder)
            return next_reminder
        return None

    async def _async_request(
        self, endpoint: str, method: str = "GET", **kwargs: Any
    ) -> Any:
        """Make an async request to the LubeLogger API."""
        url = f"{self._url}{endpoint}"
        session = self._session or aiohttp.ClientSession()

        try:
            async with session.request(
                method,
                url,
                auth=self._auth,
                timeout=aiohttp.ClientTimeout(total=10),
                **kwargs,
            ) as response:
                if response.status == 404:
                    _LOGGER.debug("Endpoint not found: %s", url)
                    return []
                response.raise_for_status()
                if response.content_type == "application/json":
                    return await response.json()
                return await response.text()
        except aiohttp.ClientError as err:
            _LOGGER.error("Error communicating with LubeLogger API: %s", err)
            raise
        finally:
            if not self._session:
                await session.close()
