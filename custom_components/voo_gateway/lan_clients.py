"""LAN client parsing helpers for VOO Gateway data."""

from __future__ import annotations

import hashlib
from typing import Any


def _first_defined(entry: dict[str, Any], keys: tuple[str, ...]) -> Any:
    """Return first non-empty field from candidate keys."""
    for key in keys:
        value = entry.get(key)
        if value not in (None, ""):
            return value
    return None


def normalize_host_entry(entry: dict[str, Any], source_index: int | None = None) -> dict[str, Any]:
    """Normalize a host table entry to a stable structure."""
    host_name = _first_defined(
        entry,
        (
            "HostName",
            "hostName",
            "Hostname",
            "DeviceName",
            "Name",
            "host",
        ),
    )
    if host_name is None:
        host_name = "Unknown"

    ip_address = _first_defined(
        entry,
        (
            "IPAddress",
            "ip",
            "IP",
            "ipaddr",
            "ipAddress",
            "IPv4Address",
            "HostIPAddress",
        ),
    )
    mac_address = _first_defined(
        entry,
        (
            "MACAddress",
            "mac",
            "MacAddress",
            "PhysAddress",
            "macAddress",
            "MAC",
            "physAddress",
        ),
    )
    interface = _first_defined(
        entry,
        (
            "Interface",
            "associateddevice",
            "AssociatedDevice",
            "connection",
            "Layer1Interface",
            "ConnectionType",
        ),
    )
    if interface is None:
        interface = "unknown"

    active = _first_defined(entry, ("Active", "active", "Status", "status"))
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
        "source_index": source_index,
    }


def normalize_mac(mac: Any) -> str | None:
    """Return a canonical MAC format if possible."""
    if not mac:
        return None

    clean = str(mac).strip().lower().replace("-", ":")
    parts = [part.zfill(2) for part in clean.split(":") if part]
    if len(parts) == 6 and all(len(part) == 2 for part in parts):
        normalized = ":".join(parts)
        if normalized == "00:00:00:00:00:00":
            return None
        return normalized
    return clean


def normalized_hosts(host_data: dict[str, Any]) -> list[dict[str, Any]]:
    """Return normalized host list from host API data."""
    host_tbl = host_data.get("hostTbl", [])
    if not isinstance(host_tbl, list):
        return []

    normalized = []
    for index, item in enumerate(host_tbl):
        if isinstance(item, dict):
            normalized.append(normalize_host_entry(item, source_index=index))

    return sorted(
        normalized,
        key=lambda x: (
            str(x.get("name") or "").lower(),
            str(x.get("ip_address") or ""),
            int(x.get("source_index") or 0),
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
    if name and str(name).strip().lower() not in {"unknown", "n/a", "none"}:
        return f"name_{str(name).strip().lower().replace(' ', '_')}"

    source_index = client.get("source_index")
    if source_index is not None:
        return f"idx_{source_index}"

    # Last resort: hash the normalized payload to avoid collisions.
    fingerprint_input = "|".join(
        [
            str(client.get("name") or ""),
            str(client.get("ip_address") or ""),
            str(client.get("mac_address") or ""),
            str(client.get("interface") or ""),
            str(client.get("active") or ""),
        ]
    )
    if fingerprint_input.strip("|"):
        digest = hashlib.sha1(fingerprint_input.encode("utf-8")).hexdigest()[:12]
        return f"hash_{digest}"

    return None
