"""The VOO Gateway integration."""

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_USERNAME, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er

from .const import CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL, DOMAIN
from .coordinator import VooGatewayDataUpdateCoordinator
from .voo_api import VooApi, VooAuthError

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [Platform.SENSOR, Platform.BINARY_SENSOR, Platform.DEVICE_TRACKER]


async def _async_cleanup_legacy_unknown_trackers(
    hass: HomeAssistant,
    entry: ConfigEntry,
) -> None:
    """Remove legacy Unknown tracker entities/devices created by old ID logic."""
    ent_reg = er.async_get(hass)
    dev_reg = dr.async_get(hass)

    remove_entity_ids: list[str] = []
    legacy_prefix = f"{entry.entry_id}_client_name_unknown"

    for entity_entry in er.async_entries_for_config_entry(ent_reg, entry.entry_id):
        if entity_entry.domain != Platform.DEVICE_TRACKER:
            continue

        unique_id = entity_entry.unique_id or ""
        looks_legacy_unknown = unique_id.startswith(legacy_prefix)
        has_unknown_name = (entity_entry.original_name or "").strip().lower() in {
            "unknown",
            "unknown device",
        }
        if looks_legacy_unknown or has_unknown_name:
            remove_entity_ids.append(entity_entry.entity_id)

    for entity_id in remove_entity_ids:
        ent_reg.async_remove(entity_id)

    # Remove orphaned legacy devices if still present.
    for device in dr.async_entries_for_config_entry(dev_reg, entry.entry_id):
        device_name = (device.name or "").strip().lower()
        has_legacy_identifier = any(
            identifier[0] == DOMAIN and str(identifier[1]).startswith(f"{entry.entry_id}_client_name_unknown")
            for identifier in device.identifiers
        )
        if has_legacy_identifier or device_name in {"unknown", "unknown device"}:
            dev_reg.async_remove_device(device.id)

    if remove_entity_ids:
        _LOGGER.info(
            "Removed %d legacy Unknown device_tracker entities for entry %s",
            len(remove_entity_ids),
            entry.entry_id,
        )


async def async_migrate_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Migrate old VOO Gateway config entries."""
    _LOGGER.debug("Migrating VOO Gateway config entry from version %s", entry.version)

    if entry.version < 2:
        await _async_cleanup_legacy_unknown_trackers(hass, entry)
        hass.config_entries.async_update_entry(entry, version=2)

    _LOGGER.debug("Migration for entry %s completed", entry.entry_id)
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up VOO Gateway from a config entry."""
    host = entry.data[CONF_HOST]
    username = entry.data[CONF_USERNAME]
    password = entry.data[CONF_PASSWORD]
    scan_interval = entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)

    _LOGGER.debug("Setting up VOO Gateway at %s", host)

    # Create API client
    api = VooApi(host, username, password)

    # Authenticate
    try:
        await api.authenticate()
    except VooAuthError as err:
        _LOGGER.error("Failed to authenticate with VOO Gateway: %s", err)
        return False

    # Create coordinator
    coordinator = VooGatewayDataUpdateCoordinator(
        hass,
        entry,
        api,
        scan_interval=scan_interval,
    )

    # Fetch initial data
    await coordinator.async_config_entry_first_refresh()

    # Store coordinator and API
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {
        "coordinator": coordinator,
        "api": api,
    }

    # Setup platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Listen for option changes
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        # Close API session
        api = hass.data[DOMAIN][entry.entry_id].get("api")
        if api:
            await api.close()

        # Remove entry data
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry when options change."""
    await hass.config_entries.async_reload(entry.entry_id)
