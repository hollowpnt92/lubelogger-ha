"""Client for interacting with LubeLogger API."""
from __future__ import annotations

import logging
from typing import Any

import aiohttp

from .const import (
    API_GAS_RECORD,
    API_ODOMETER,
    API_PLAN,
    API_REMINDER,
    API_REPAIR_RECORD,
    API_ROOT,
    API_SERVICE_RECORD,
    API_SUPPLY_RECORD,
    API_TAX,
    API_UPGRADE_RECORD,
    API_VEHICLES,
)

_LOGGER = logging.getLogger(__name__)


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
        endpoint = f"{API_ODOMETER}?vehicleId={vehicle_id}" if vehicle_id else API_ODOMETER
        records = await self._async_request(endpoint)
        if not isinstance(records, list) or not records:
            _LOGGER.debug("No odometer records found for vehicle %s", vehicle_id)
            return None

        def sort_key(rec: dict[str, Any]) -> Any:
            # Sort by id (numeric) - higher id = more recent
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
        
        # Sort by dateCreated to get the most recent/next one
        def sort_key(rec: dict[str, Any]) -> Any:
            date_str = rec.get("dateCreated") or rec.get("dateModified") or rec.get("Date") or rec.get("date")
            if date_str:
                return date_str
            return ""
        
        sorted_records = sorted([r for r in records if sort_key(r)], key=sort_key)
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
            # Sort by id (numeric) - higher id = more recent
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
            # Sort by id (numeric) - higher id = more recent
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

        # Sort by dueDate to get the next one
        def sort_key(rec: dict[str, Any]) -> Any:
            date_str = rec.get("dueDate") or rec.get("DueDate") or rec.get("Date") or rec.get("date")
            if date_str:
                return date_str
            return ""

        sorted_records = sorted([r for r in records if sort_key(r)], key=sort_key)
        if sorted_records:
            _LOGGER.debug("Next reminder for vehicle %s: %s", vehicle_id, sorted_records[0])
            return sorted_records[0]
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
                    # Endpoint not found; log as debug and return empty result
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

