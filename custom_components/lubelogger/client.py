"""Client for interacting with LubeLogger API."""
from __future__ import annotations

import logging
from typing import Any

import aiohttp

from .const import (
    API_ODOMETER,
    API_PLAN,
    API_ROOT,
    API_SERVICE_RECORD,
    API_TAX,
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
        endpoint = API_ODOMETER
        if vehicle_id:
            endpoint = f"{API_ODOMETER}?vehicleId={vehicle_id}"
        records = await self._async_request(endpoint)
        if not isinstance(records, list) or not records:
            _LOGGER.debug("No odometer records found for vehicle %s", vehicle_id)
            return None
        
        # Filter by vehicle if query param didn't work (check multiple field name variations)
        if vehicle_id:
            filtered = [
                r for r in records
                if r.get("VehicleId") == vehicle_id
                or r.get("vehicleId") == vehicle_id
                or r.get("Vehicle") == vehicle_id
                or r.get("vehicle") == vehicle_id
            ]
            if not filtered:
                _LOGGER.debug("No odometer records found for vehicle %s after filtering", vehicle_id)
                return None
            records = filtered

        def sort_key(rec: dict[str, Any]) -> Any:
            # Try to sort by Id (numeric) or Date (datetime)
            rec_id = rec.get("Id") or rec.get("id")
            rec_date = rec.get("Date") or rec.get("date")
            if rec_id:
                try:
                    return int(rec_id)
                except (ValueError, TypeError):
                    return rec_id
            if rec_date:
                return rec_date
            return 0

        latest = sorted(records, key=sort_key)[-1]
        _LOGGER.debug("Latest odometer for vehicle %s: %s", vehicle_id, latest)
        return latest

    async def async_get_next_plan(
        self, vehicle_id: int | None = None
    ) -> dict[str, Any] | None:
        """Get the next upcoming plan item for a vehicle."""
        endpoint = API_PLAN
        if vehicle_id:
            endpoint = f"{API_PLAN}?vehicleId={vehicle_id}"
        records = await self._async_request(endpoint)
        if not isinstance(records, list) or not records:
            _LOGGER.debug("No plan records found for vehicle %s", vehicle_id)
            return None
        
        # Filter by vehicle if query param didn't work
        if vehicle_id:
            filtered = [
                r for r in records
                if r.get("VehicleId") == vehicle_id
                or r.get("vehicleId") == vehicle_id
                or r.get("Vehicle") == vehicle_id
                or r.get("vehicle") == vehicle_id
            ]
            if not filtered:
                _LOGGER.debug("No plan records found for vehicle %s after filtering", vehicle_id)
                return None
            records = filtered
        
        # Sort by due date to get the next one
        def sort_key(rec: dict[str, Any]) -> Any:
            date_str = rec.get("DueDate") or rec.get("dueDate") or rec.get("Date") or rec.get("date")
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
        endpoint = API_TAX
        if vehicle_id:
            endpoint = f"{API_TAX}?vehicleId={vehicle_id}"
        records = await self._async_request(endpoint)
        if not isinstance(records, list) or not records:
            _LOGGER.debug("No tax records found for vehicle %s", vehicle_id)
            return None

        # Filter by vehicle if query param didn't work
        if vehicle_id:
            filtered = [
                r for r in records
                if r.get("VehicleId") == vehicle_id
                or r.get("vehicleId") == vehicle_id
                or r.get("Vehicle") == vehicle_id
                or r.get("vehicle") == vehicle_id
            ]
            if not filtered:
                _LOGGER.debug("No tax records found for vehicle %s after filtering", vehicle_id)
                return None
            records = filtered

        def sort_key(rec: dict[str, Any]) -> Any:
            rec_id = rec.get("Id") or rec.get("id")
            rec_date = rec.get("Date") or rec.get("date")
            if rec_id:
                try:
                    return int(rec_id)
                except (ValueError, TypeError):
                    return rec_id
            if rec_date:
                return rec_date
            return 0

        latest = sorted(records, key=sort_key)[-1]
        _LOGGER.debug("Latest tax for vehicle %s: %s", vehicle_id, latest)
        return latest

    async def async_get_latest_service(
        self, vehicle_id: int | None = None
    ) -> dict[str, Any] | None:
        """Get the latest service record for a vehicle."""
        endpoint = API_SERVICE_RECORD
        if vehicle_id:
            endpoint = f"{API_SERVICE_RECORD}?vehicleId={vehicle_id}"
        records = await self._async_request(endpoint)
        if not isinstance(records, list) or not records:
            _LOGGER.debug("No service records found for vehicle %s", vehicle_id)
            return None

        # Filter by vehicle if query param didn't work
        if vehicle_id:
            filtered = [
                r for r in records
                if r.get("VehicleId") == vehicle_id
                or r.get("vehicleId") == vehicle_id
                or r.get("Vehicle") == vehicle_id
                or r.get("vehicle") == vehicle_id
            ]
            if not filtered:
                _LOGGER.debug("No service records found for vehicle %s after filtering", vehicle_id)
                return None
            records = filtered

        def sort_key(rec: dict[str, Any]) -> Any:
            rec_id = rec.get("Id") or rec.get("id")
            rec_date = rec.get("Date") or rec.get("date")
            if rec_id:
                try:
                    return int(rec_id)
                except (ValueError, TypeError):
                    return rec_id
            if rec_date:
                return rec_date
            return 0

        latest = sorted(records, key=sort_key)[-1]
        _LOGGER.debug("Latest service for vehicle %s: %s", vehicle_id, latest)
        return latest

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

