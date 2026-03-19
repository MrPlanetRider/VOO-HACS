"""Device tracker entities for VOO Gateway LAN clients."""

from __future__ import annotations

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

    @callback
    def _add_new_client_entities() -> None:
        data = coordinator.data or {}
        clients = normalized_hosts(data.get("host", {}))

        new_entities: list[VooGatewayClientTracker] = []
        for client in clients:
            client_id = stable_client_id(client)
            if not client_id or client_id in known_ids:
                continue
            known_ids.add(client_id)
            new_entities.append(
                VooGatewayClientTracker(
                    coordinator=coordinator,
                    entry=entry,
                    client_id=client_id,
                )
            )

        if new_entities:
            async_add_entities(new_entities)

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
    ) -> None:
        """Initialize the tracker entity."""
        super().__init__(coordinator)
        self.entry = entry
        self.client_id = client_id
        self._attr_unique_id = f"{entry.entry_id}_client_{client_id}"

    def _current_client(self) -> dict[str, Any] | None:
        """Return latest normalized client data for this tracker."""
        data = self.coordinator.data or {}
        clients = normalized_hosts(data.get("host", {}))
        for client in clients:
            if stable_client_id(client) == self.client_id:
                return client
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
        """Return the display name of this client."""
        client = self._current_client()
        if client and client.get("name"):
            return str(client["name"])
        return f"LAN Client {self.client_id.replace('_', ' ')}"

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
        client = self._current_client() or {}
        mac = client.get("mac_address")

        info: DeviceInfo = {
            "identifiers": {(DOMAIN, f"{self.entry.entry_id}_client_{self.client_id}")},
            "name": str(client.get("name") or self.name),
            "via_device": (DOMAIN, self.entry.entry_id),
        }
        if mac:
            info["connections"] = {(dr.CONNECTION_NETWORK_MAC, str(mac))}
        return info
