"""Client for interacting with LubeLogger API."""
from __future__ import annotations

import logging
from typing import Any

import aiohttp

from .const import (
    API_FUEL,
    API_MAINTENANCE,
    API_STATS,
    API_VEHICLES,
    CONF_PASSWORD,
    CONF_URL,
    CONF_USERNAME,
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
        return await self._async_request(API_VEHICLES)

    async def async_get_maintenance_records(
        self, vehicle_id: int | None = None
    ) -> list[dict[str, Any]]:
        """Get maintenance records."""
        url = API_MAINTENANCE
        if vehicle_id:
            url = f"{url}?vehicleId={vehicle_id}"
        return await self._async_request(url)

    async def async_get_fuel_records(
        self, vehicle_id: int | None = None
    ) -> list[dict[str, Any]]:
        """Get fuel records."""
        url = API_FUEL
        if vehicle_id:
            url = f"{url}?vehicleId={vehicle_id}"
        return await self._async_request(url)

    async def async_get_vehicle_statistics(
        self, vehicle_id: int
    ) -> dict[str, Any]:
        """Get vehicle statistics."""
        return await self._async_request(f"{API_STATS}?vehicleId={vehicle_id}")

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

