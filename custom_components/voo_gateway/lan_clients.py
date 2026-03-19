"""LAN client parsing helpers for VOO Gateway data."""

from __future__ import annotations

import hashlib
import re
from typing import Any

_IPV4_PATTERN = re.compile(r"^(?:\d{1,3}\.){3}\d{1,3}$")
_MAC_PATTERN = re.compile(r"^(?:[0-9a-fA-F]{2}[:-]){5}[0-9a-fA-F]{2}$")


def _first_defined(entry: dict[str, Any], keys: tuple[str, ...]) -> Any:
    """Return first non-empty field from candidate keys."""
    for key in keys:
        value = entry.get(key)
        if value not in (None, ""):
            return value
    return None


def _normalize_str(value: Any) -> str | None:
    """Normalize any value to stripped string or None."""
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _find_ip_address(entry: dict[str, Any]) -> str | None:
    """Find IPv4 value from known keys or heuristic scan."""
    direct = _first_defined(
        entry,
        (
            "IPAddress",
            "ip",
            "IP",
            "ipaddr",
            "ipAddress",
            "IPv4Address",
            "HostIPAddress",
            "Addr",
            "address",
        ),
    )
    text = _normalize_str(direct)
    if text and _IPV4_PATTERN.match(text):
        return text

    for key, value in entry.items():
        key_l = str(key).lower()
        if "ip" not in key_l and "addr" not in key_l:
            continue
        text = _normalize_str(value)
        if text and _IPV4_PATTERN.match(text):
            return text
    return None


def _find_mac_address(entry: dict[str, Any]) -> str | None:
    """Find MAC value from known keys or heuristic scan."""
    direct = _first_defined(
        entry,
        (
            "MACAddress",
            "mac",
            "MacAddress",
            "PhysAddress",
            "macAddress",
            "MAC",
            "physAddress",
            "HWAddress",
        ),
    )
    text = _normalize_str(direct)
    if text and _MAC_PATTERN.match(text.replace("-", ":")):
        return text

    for key, value in entry.items():
        key_l = str(key).lower()
        if "mac" not in key_l and "phys" not in key_l and "hw" not in key_l:
            continue
        text = _normalize_str(value)
        if text and _MAC_PATTERN.match(text.replace("-", ":")):
            return text
    return None


def _find_host_name(entry: dict[str, Any]) -> str:
    """Find best host display name from known keys or heuristic scan."""
    direct = _first_defined(
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
    text = _normalize_str(direct)
    if text:
        return text

    for key, value in entry.items():
        key_l = str(key).lower()
        if not any(token in key_l for token in ("name", "host", "device")):
            continue
        if any(token in key_l for token in ("interface", "status", "type")):
            continue
        text = _normalize_str(value)
        if text:
            return text

    return "Unknown"


def normalize_host_entry(entry: dict[str, Any], source_index: int | None = None) -> dict[str, Any]:
    """Normalize a host table entry to a stable structure."""
    host_name = _find_host_name(entry)
    ip_address = _find_ip_address(entry)
    mac_address = _find_mac_address(entry)
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
