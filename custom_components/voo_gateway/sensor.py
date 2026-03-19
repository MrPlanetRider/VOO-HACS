"""Sensors for VOO Gateway."""

import logging
from typing import Any

from homeassistant.components.sensor import SensorEntity, SensorEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import VooGatewayDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


def _normalize_host_entry(entry: dict[str, Any]) -> dict[str, Any]:
    """Normalize a host table entry to a stable structure."""
    host_name = (
        entry.get("HostName")
        or entry.get("hostName")
        or entry.get("Hostname")
        or "Unknown"
    )
    ip_address = (
        entry.get("IPAddress")
        or entry.get("ip")
        or entry.get("IP")
        or entry.get("ipaddr")
    )
    mac_address = (
        entry.get("MACAddress")
        or entry.get("mac")
        or entry.get("MacAddress")
        or entry.get("PhysAddress")
    )
    interface = (
        entry.get("Interface")
        or entry.get("associateddevice")
        or entry.get("AssociatedDevice")
        or entry.get("connection")
        or "unknown"
    )
    active = entry.get("Active")
    if isinstance(active, str):
        active = active.strip().lower() in {"true", "1", "yes", "up", "active"}
    elif isinstance(active, bool):
        active = active
    else:
        active = None

    interface_str = str(interface).lower()
    if any(token in interface_str for token in ("wifi", "wlan", "wireless")):
        connection_type = "wireless"
    elif any(token in interface_str for token in ("ethernet", "eth", "lan")):
        connection_type = "wired"
    else:
        connection_type = "unknown"

    return {
        "name": host_name,
        "ip_address": ip_address,
        "mac_address": mac_address,
        "interface": interface,
        "connection_type": connection_type,
        "active": active,
    }


def _normalized_hosts(host_data: dict[str, Any]) -> list[dict[str, Any]]:
    """Return normalized host list from host API data."""
    host_tbl = host_data.get("hostTbl", [])
    if not isinstance(host_tbl, list):
        return []
    normalized = [
        _normalize_host_entry(item)
        for item in host_tbl
        if isinstance(item, dict)
    ]
    return sorted(
        normalized,
        key=lambda x: (
            str(x.get("name") or "").lower(),
            str(x.get("ip_address") or ""),
        ),
    )


SENSOR_DESCRIPTIONS = [
    SensorEntityDescription(
        key="uptime",
        name="Uptime",
        native_unit_of_measurement=UnitOfTime.SECONDS,
        icon="mdi:clock-outline",
    ),
    SensorEntityDescription(
        key="local_time",
        name="Local Time",
        icon="mdi:clock",
    ),
    SensorEntityDescription(
        key="model_name",
        name="Model",
        icon="mdi:information",
    ),
    SensorEntityDescription(
        key="firmware_name",
        name="Firmware Version",
        icon="mdi:information",
    ),
    SensorEntityDescription(
        key="hardware_version",
        name="Hardware Version",
        icon="mdi:information",
    ),
    SensorEntityDescription(
        key="wan_ip",
        name="WAN IP Address",
        icon="mdi:ip",
    ),
    SensorEntityDescription(
        key="lan_ip",
        name="LAN IP Address",
        icon="mdi:ip",
    ),
    SensorEntityDescription(
        key="lan_subnet",
        name="LAN Subnet Mask",
        icon="mdi:ip",
    ),
    SensorEntityDescription(
        key="gateway_ip",
        name="Gateway IP",
        icon="mdi:ip",
    ),
    SensorEntityDescription(
        key="dns_servers",
        name="DNS Servers",
        icon="mdi:dns",
    ),
    SensorEntityDescription(
        key="connected_devices",
        name="Connected Devices",
        icon="mdi:network",
    ),
    SensorEntityDescription(
        key="connected_wired_devices",
        name="Connected Wired Devices",
        icon="mdi:ethernet",
    ),
    SensorEntityDescription(
        key="connected_wireless_devices",
        name="Connected Wireless Devices",
        icon="mdi:wifi",
    ),
    SensorEntityDescription(
        key="connected_active_devices",
        name="Connected Active Devices",
        icon="mdi:check-network",
    ),
]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up sensor entities from a config entry."""
    coordinator: VooGatewayDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id][
        "coordinator"
    ]

    entities = [
        VooGatewaySensor(coordinator, entry, description)
        for description in SENSOR_DESCRIPTIONS
    ]

    async_add_entities(entities)


class VooGatewaySensor(CoordinatorEntity[VooGatewayDataUpdateCoordinator], SensorEntity):
    """Represents a VOO Gateway sensor."""

    entity_description: SensorEntityDescription

    def __init__(
        self,
        coordinator: VooGatewayDataUpdateCoordinator,
        entry: ConfigEntry,
        description: SensorEntityDescription,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"
        self.entry = entry

    @property
    def native_value(self) -> Any:
        """Return the state of the sensor."""
        data = self.coordinator.data or {}

        key = self.entity_description.key
        system = data.get("system", {})
        dhcp = data.get("dhcp", {})
        host = data.get("host", {})
        devices = _normalized_hosts(host)

        if key == "uptime":
            return system.get("UpTime")
        elif key == "local_time":
            return system.get("LocalTime")
        elif key == "model_name":
            return system.get("ModelName")
        elif key == "firmware_name":
            return system.get("FirmwareName")
        elif key == "hardware_version":
            return system.get("HardwareVersion")
        elif key == "wan_ip":
            return dhcp.get("IPAddressRT")
        elif key == "lan_ip":
            return dhcp.get("LanIPAddress")
        elif key == "lan_subnet":
            return dhcp.get("LanSubnetMask")
        elif key == "gateway_ip":
            return dhcp.get("IPAddressGW")
        elif key == "dns_servers":
            dns_list = dhcp.get("DNSTblRT", [])
            if isinstance(dns_list, list):
                return ", ".join(dns_list)
            return dns_list
        elif key == "connected_devices":
            return len(devices)
        elif key == "connected_wired_devices":
            return len([x for x in devices if x.get("connection_type") == "wired"])
        elif key == "connected_wireless_devices":
            return len([x for x in devices if x.get("connection_type") == "wireless"])
        elif key == "connected_active_devices":
            return len([x for x in devices if x.get("active") is True])
        return None

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return extra state attributes for selected sensors."""
        if self.entity_description.key != "connected_devices":
            return None

        data = self.coordinator.data or {}
        host = data.get("host", {})
        devices = _normalized_hosts(host)

        return {
            "devices": devices,
            "device_count": len(devices),
            "wired_count": len([x for x in devices if x.get("connection_type") == "wired"]),
            "wireless_count": len(
                [x for x in devices if x.get("connection_type") == "wireless"]
            ),
            "active_count": len([x for x in devices if x.get("active") is True]),
        }

    @property
    def device_info(self):
        """Return device information."""
        system = self.coordinator.data.get("system", {})
        return {
            "identifiers": {(DOMAIN, self.entry.entry_id)},
            "name": "VOO Gateway",
            "manufacturer": "Technicolor",
            "model": system.get("ModelName", "Unknown"),
            "sw_version": system.get("FirmwareName", "Unknown"),
            "configuration_url": f"http://{self.entry.data.get('host')}",
        }
