"""System health support for VOO Gateway integration."""

from __future__ import annotations

from typing import Any

from homeassistant.components import system_health
from homeassistant.core import HomeAssistant, callback

from .const import DOMAIN
from .lan_clients import normalized_clients


def _first_defined(mapping: dict[str, Any], keys: tuple[str, ...]) -> Any:
    """Return first non-None value for candidate keys."""
    for key in keys:
        value = mapping.get(key)
        if value is not None:
            return value
    return None


@callback
def async_register(
    hass: HomeAssistant,
    register: system_health.SystemHealthRegistration,
) -> None:
    """Register system health callbacks."""
    register.async_register_info(system_health_info)


async def system_health_info(hass: HomeAssistant) -> dict[str, Any]:
    """Return info for the system health page."""
    domain_data = hass.data.get(DOMAIN, {})
    if not domain_data:
        return {
            "configured_entries": 0,
            "status": "not_configured",
        }

    entry_id, entry_data = next(iter(domain_data.items()))
    coordinator = entry_data.get("coordinator")

    if coordinator is None:
        return {
            "configured_entries": len(domain_data),
            "status": "coordinator_missing",
        }

    data = coordinator.data or {}
    system = data.get("system", {})
    modem = data.get("modem", {})
    clients = normalized_clients(data.get("host", {}), data.get("dhcp", {}))

    info: dict[str, Any] = {
        "configured_entries": len(domain_data),
        "active_entry_id": entry_id,
        "gateway_host": coordinator.api.host,
        "last_update_success": coordinator.last_update_success,
        "last_exception": str(coordinator.last_exception)
        if coordinator.last_exception
        else None,
        "connected_clients": len(clients),
        "connected_clients_active": len([x for x in clients if x.get("active") is True]),
    }

    model = system.get("ModelName")
    firmware = system.get("FirmwareName")
    cm_status = system.get("CMStatus")
    if model:
        info["model"] = model
    if firmware:
        info["firmware"] = firmware
    if cm_status:
        info["cable_modem_status"] = cm_status

    modem_status = modem.get("ModemStatus")
    if modem_status:
        info["modem_status"] = modem_status

    cpu_usage = _first_defined(system, ("CPUUsage", "CpuUsage", "ProcessorUsage"))
    if cpu_usage is not None:
        info["cpu_usage"] = cpu_usage

    mem_total = _first_defined(system, ("MemTotal", "MemoryTotal"))
    if mem_total is not None:
        info["memory_total"] = mem_total

    mem_free = _first_defined(system, ("MemFree", "MemoryFree"))
    if mem_free is not None:
        info["memory_free"] = mem_free

    processor_speed = _first_defined(system, ("ProcessorSpeed", "CpuSpeed"))
    if processor_speed is not None:
        info["processor_speed"] = processor_speed

    bootloader_version = _first_defined(
        system,
        ("BootloaderVersion", "BootLoaderVersion"),
    )
    if bootloader_version is not None:
        info["bootloader_version"] = bootloader_version

    return info
