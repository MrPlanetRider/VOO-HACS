"""LAN client parsing helpers for VOO Gateway data."""

from __future__ import annotations

from typing import Any


def normalize_host_entry(entry: dict[str, Any]) -> dict[str, Any]:
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
    elif not isinstance(active, bool):
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
        "mac_address": normalize_mac(mac_address),
        "interface": interface,
        "connection_type": connection_type,
        "active": active,
    }


def normalize_mac(mac: Any) -> str | None:
    """Return a canonical MAC format if possible."""
    if not mac:
        return None

    clean = str(mac).strip().lower().replace("-", ":")
    parts = [part.zfill(2) for part in clean.split(":") if part]
    if len(parts) == 6 and all(len(part) == 2 for part in parts):
        return ":".join(parts)
    return clean


def normalized_hosts(host_data: dict[str, Any]) -> list[dict[str, Any]]:
    """Return normalized host list from host API data."""
    host_tbl = host_data.get("hostTbl", [])
    if not isinstance(host_tbl, list):
        return []

    normalized = [
        normalize_host_entry(item)
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


def stable_client_id(client: dict[str, Any]) -> str | None:
    """Build a stable client id for entities from normalized client data."""
    mac = client.get("mac_address")
    if mac:
        return f"mac_{str(mac).replace(':', '')}"

    ip = client.get("ip_address")
    if ip:
        return f"ip_{ip}"

    name = client.get("name")
    if name:
        return f"name_{str(name).strip().lower().replace(' ', '_')}"

    return None
