"""Device tracker entities for VOO Gateway LAN clients."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.device_tracker import SourceType
from homeassistant.components.device_tracker.config_entry import TrackerEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import VooGatewayDataUpdateCoordinator
from .lan_clients import normalized_hosts, stable_client_id

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up device tracker entities from a config entry."""
    coordinator: VooGatewayDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id][
        "coordinator"
    ]

    known_ids: set[str] = set()
    known_clients: dict[str, dict[str, Any]] = {}

    @callback
    def _add_new_client_entities() -> None:
        data = coordinator.data or {}
        clients = normalized_hosts(data.get("host", {}))
        _LOGGER.debug(
            "Device tracker discovery: found %d clients from coordinator (entry_id=%s)",
            len(clients),
            entry.entry_id,
        )

        new_entities: list[VooGatewayClientTracker] = []
        for idx, client in enumerate(clients):
            client_id = stable_client_id(client)
            if not client_id:
                # Fallback: create ID from index if stable_client_id fails
                client_id = f"client_{idx}"
                _LOGGER.debug("No stable ID for client %s, using fallback: %s", client, client_id)
            
            if client_id in known_ids:
                # Update cached client data for existing trackers
                known_clients[client_id] = client
                continue
            
            known_ids.add(client_id)
            known_clients[client_id] = client
            entity = VooGatewayClientTracker(
                coordinator=coordinator,
                entry=entry,
                client_id=client_id,
                client_data=client,
            )
            new_entities.append(entity)
            _LOGGER.info(
                "Creating device tracker %s: name=%s, mac=%s, ip=%s",
                client_id,
                client.get("name"),
                client.get("mac_address"),
                client.get("ip_address"),
            )

        if new_entities:
            _LOGGER.info("Adding %d new device tracker entities", len(new_entities))
            async_add_entities(new_entities)
        else:
            if not known_ids:
                _LOGGER.warning(
                    "No device tracker entities created - coordinator returned %d clients",
                    len(clients),
                )

    _add_new_client_entities()
    entry.async_on_unload(coordinator.async_add_listener(_add_new_client_entities))


class VooGatewayClientTracker(
    CoordinatorEntity[VooGatewayDataUpdateCoordinator], TrackerEntity
):
    """Tracker entity representing one LAN client from the gateway host table."""

    _attr_source_type = SourceType.ROUTER

    def __init__(
        self,
        coordinator: VooGatewayDataUpdateCoordinator,
        entry: ConfigEntry,
        client_id: str,
        client_data: dict[str, Any] | None = None,
    ) -> None:
        """Initialize the tracker entity."""
        super().__init__(coordinator)
        self.entry = entry
        self.client_id = client_id
        self._attr_unique_id = f"{entry.entry_id}_client_{client_id}"
        self._cached_client_data = client_data or {}
        
        # Set a deterministic name from the cached data or client_id
        self._attr_name = self._build_name_from_client(self._cached_client_data)
        
        _LOGGER.debug(
            "Initialized device tracker %s with name: %s",
            self.client_id,
            self._attr_name,
        )

    def _build_name_from_client(self, client: dict[str, Any]) -> str:
        """Build a deterministic name from client data."""
        if not client:
            return str(self.client_id).replace("_", " ").title()
        
        # Try hostname first
        if client.get("name"):
            name_str = str(client.get("name")).strip()
            if name_str and name_str.lower() not in {"unknown", "n/a", "none"}:
                return name_str
        
        # Try IP address
        if client.get("ip_address"):
            ip = str(client.get("ip_address")).strip()
            if ip:
                return f"Device {ip}"
        
        # Try MAC address
        if client.get("mac_address"):
            mac = str(client.get("mac_address")).strip()
            if mac:
                return f"Device {mac}"
        
        # Fallback
        return str(self.client_id).replace("_", " ").title()

    def _current_client(self) -> dict[str, Any] | None:
        """Return latest normalized client data for this tracker."""
        # Try to find in current coordinator data first
        data = self.coordinator.data or {}
        clients = normalized_hosts(data.get("host", {}))
        for client in clients:
            if stable_client_id(client) == self.client_id:
                self._cached_client_data = client
                return client
        
        # Fallback to cached data if no match found
        if self._cached_client_data:
            _LOGGER.debug(
                "Using cached client data for %s (no match in current coordinator data)",
                self.client_id,
            )
            return self._cached_client_data
        
        return None

    @property
    def is_connected(self) -> bool:
        """Return whether this client is currently connected."""
        client = self._current_client()
        if client is None:
            return False

        active = client.get("active")
        if isinstance(active, bool):
            return active
        return True

    @property
    def name(self) -> str:
        """Return the display name of this client (used by HA when _attr_name not set)."""
        # Update _attr_name from current client if possible
        client = self._current_client()
        if client:
            self._attr_name = self._build_name_from_client(client)
        return self._attr_name

    @property
    def mac_address(self) -> str | None:
        """Return MAC address of this client if available."""
        client = self._current_client()
        if not client:
            return None
        mac = client.get("mac_address")
        return str(mac) if mac else None

    @property
    def ip_address(self) -> str | None:
        """Return IP address of this client if available."""
        client = self._current_client()
        if not client:
            return None
        ip = client.get("ip_address")
        return str(ip) if ip else None

    @property
    def hostname(self) -> str | None:
        """Return hostname for this client if available."""
        client = self._current_client()
        if not client:
            return None
        name = client.get("name")
        return str(name) if name else None

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return extra metadata about the client connection."""
        client = self._current_client()
        if not client:
            return None
        return {
            "connection_type": client.get("connection_type"),
            "interface": client.get("interface"),
            "active": client.get("active"),
        }

    @property
    def device_info(self) -> DeviceInfo:
        """Return device registry information for this tracked client."""
        client = self._current_client()
        
        # Use the same name as the entity itself for consistency
        device_name = self._attr_name or self._build_name_from_client(client or {})
        
        # Build device identifiers and connections
        identifiers = {(DOMAIN, f"{self.entry.entry_id}_client_{self.client_id}")}
        connections: set[tuple[str, str]] = set()
        
        if client:
            mac = client.get("mac_address")
            if mac:
                mac_str = str(mac).strip()
                if mac_str:
                    connections.add((dr.CONNECTION_NETWORK_MAC, mac_str))

        info: DeviceInfo = {
            "identifiers": identifiers,
            "name": device_name,
            "via_device": (DOMAIN, self.entry.entry_id),
        }
        if connections:
            info["connections"] = connections
        
        _LOGGER.debug(
            "Device info for %s: name=%s, has_mac=%s, via_device=%s",
            self.client_id,
            device_name,
            bool(connections),
            self.entry.entry_id,
        )
        
        return info
