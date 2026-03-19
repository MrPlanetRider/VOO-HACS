"""Sensors for VOO Gateway."""

import logging
from typing import Any

from homeassistant.components.sensor import SensorEntity, SensorEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import VooGatewayDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


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
            host_tbl = host.get("hostTbl", [])
            if isinstance(host_tbl, list):
                return len(host_tbl)
            return 0
        return None

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
