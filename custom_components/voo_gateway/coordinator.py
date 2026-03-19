"""Data coordinator for VOO Gateway."""

import logging
from datetime import timedelta
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN
from .voo_api import VooApi

_LOGGER = logging.getLogger(__name__)


class VooGatewayDataUpdateCoordinator(DataUpdateCoordinator):
    """Data coordinator for VOO Gateway."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        api: VooApi,
        scan_interval: int = 300,
    ):
        """Initialize coordinator.

        Args:
            hass: Home Assistant instance
            entry: Config entry for this integration instance
            api: VOO API client
            scan_interval: Update interval in seconds
        """
        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name=DOMAIN,
            update_interval=timedelta(seconds=scan_interval),
        )
        self.api = api

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from VOO Gateway.

        Returns:
            Dict with system, dhcp, and host data

        Raises:
            UpdateFailed: If update fails
        """
        try:
            data = {}

            # Fetch system info
            try:
                data["system"] = await self.api.get_system_info()
            except Exception as e:
                _LOGGER.warning("Failed to fetch system info: %s", e)
                data["system"] = {}

            # Fetch DHCP config
            try:
                data["dhcp"] = await self.api.get_dhcp_config()
            except Exception as e:
                _LOGGER.warning("Failed to fetch DHCP config: %s", e)
                data["dhcp"] = {}

            # Fetch connected devices
            try:
                data["host"] = await self.api.get_connected_devices()
            except Exception as e:
                _LOGGER.warning("Failed to fetch connected devices: %s", e)
                data["host"] = {}

            # Fetch WiFi info
            try:
                data["wifi"] = await self.api.get_wifi_info()
            except Exception as e:
                _LOGGER.warning("Failed to fetch WiFi info: %s", e)
                data["wifi"] = {}

            # Fetch modem info
            try:
                data["modem"] = await self.api.get_modem_info()
            except Exception as e:
                _LOGGER.warning("Failed to fetch modem info: %s", e)
                data["modem"] = {}

            return data

        except Exception as err:
            raise UpdateFailed(f"Error communicating with VOO Gateway: {err}") from err
