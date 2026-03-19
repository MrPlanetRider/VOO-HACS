"""Sensors for VOO Gateway."""

import logging
import re
from typing import Any

from homeassistant.components.sensor import SensorEntity, SensorEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE, UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import VooGatewayDataUpdateCoordinator
from .lan_clients import normalized_hosts

_LOGGER = logging.getLogger(__name__)


def _parse_float(value: Any) -> float | None:
    """Parse numeric value from raw API field."""
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        match = re.search(r"-?\d+(?:\.\d+)?", value)
        if match:
            try:
                return float(match.group(0))
            except ValueError:
                return None
    return None


def _first_defined(mapping: dict[str, Any], keys: tuple[str, ...]) -> Any:
    """Return the first non-None value for a list of keys."""
    for key in keys:
        value = mapping.get(key)
        if value is not None:
            return value
    return None


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
    SensorEntityDescription(
        key="cpu_usage",
        name="CPU Usage",
        native_unit_of_measurement=PERCENTAGE,
        icon="mdi:cpu-64-bit",
    ),
    SensorEntityDescription(
        key="memory_total",
        name="Memory Total",
        native_unit_of_measurement="KB",
        icon="mdi:memory",
    ),
    SensorEntityDescription(
        key="memory_free",
        name="Memory Free",
        native_unit_of_measurement="KB",
        icon="mdi:memory",
    ),
    SensorEntityDescription(
        key="memory_free_percentage",
        name="Memory Free Percentage",
        native_unit_of_measurement=PERCENTAGE,
        icon="mdi:percent",
    ),
    SensorEntityDescription(
        key="processor_speed",
        name="Processor Speed",
        icon="mdi:speedometer",
    ),
    SensorEntityDescription(
        key="bootloader_version",
        name="Bootloader Version",
        icon="mdi:chip",
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
        devices = normalized_hosts(host)

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
        elif key == "cpu_usage":
            raw_cpu = _first_defined(system, ("CPUUsage", "CpuUsage", "ProcessorUsage"))
            cpu = _parse_float(raw_cpu)
            if cpu is None:
                return None
            if isinstance(raw_cpu, (int, float)) and 0 <= cpu <= 1:
                return round(cpu * 100, 1)
            return round(cpu, 1)
        elif key == "memory_total":
            mem_total = _parse_float(_first_defined(system, ("MemTotal", "MemoryTotal")))
            if mem_total is None:
                return None
            return round(mem_total, 1)
        elif key == "memory_free":
            mem_free = _parse_float(_first_defined(system, ("MemFree", "MemoryFree")))
            if mem_free is None:
                return None
            return round(mem_free, 1)
        elif key == "memory_free_percentage":
            mem_total = _parse_float(_first_defined(system, ("MemTotal", "MemoryTotal")))
            mem_free = _parse_float(_first_defined(system, ("MemFree", "MemoryFree")))
            if not mem_total or mem_total <= 0 or mem_free is None:
                return None
            return round((mem_free / mem_total) * 100, 1)
        elif key == "processor_speed":
            return _first_defined(system, ("ProcessorSpeed", "CpuSpeed"))
        elif key == "bootloader_version":
            return _first_defined(system, ("BootloaderVersion", "BootLoaderVersion"))
        return None

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return extra state attributes for selected sensors."""
        if self.entity_description.key != "connected_devices":
            return None

        data = self.coordinator.data or {}
        host = data.get("host", {})
        devices = normalized_hosts(host)

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
