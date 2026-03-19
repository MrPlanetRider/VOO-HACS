"""Binary sensors for VOO Gateway."""

import logging

from homeassistant.components.binary_sensor import (
    BinarySensorEntity,
    BinarySensorEntityDescription,
    BinarySensorDeviceClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import VooGatewayDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


BINARY_SENSOR_DESCRIPTIONS = [
    BinarySensorEntityDescription(
        key="modem_status",
        name="Modem Status",
        device_class=BinarySensorDeviceClass.CONNECTIVITY,
    ),
]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up binary sensor entities from a config entry."""
    coordinator: VooGatewayDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id][
        "coordinator"
    ]

    entities = [
        VooGatewayBinarySensor(coordinator, entry, description)
        for description in BINARY_SENSOR_DESCRIPTIONS
    ]

    async_add_entities(entities)


class VooGatewayBinarySensor(
    CoordinatorEntity[VooGatewayDataUpdateCoordinator], BinarySensorEntity
):
    """Represents a VOO Gateway binary sensor."""

    entity_description: BinarySensorEntityDescription

    def __init__(
        self,
        coordinator: VooGatewayDataUpdateCoordinator,
        entry: ConfigEntry,
        description: BinarySensorEntityDescription,
    ) -> None:
        """Initialize the binary sensor."""
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"
        self.entry = entry

    @property
    def is_on(self) -> bool | None:
        """Return the state of the binary sensor."""
        data = self.coordinator.data or {}

        key = self.entity_description.key
        system = data.get("system", {})

        if key == "modem_status":
            # Modem is up if we got data
            status = system.get("CMStatus", "")
            return status == "OK" or (data and len(data) > 0)

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
