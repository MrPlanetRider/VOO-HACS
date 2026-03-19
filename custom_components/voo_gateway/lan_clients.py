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
        "comment": _normalize_str(_first_defined(entry, ("Comment", "comment", "Description"))),
        "raw_id": _normalize_str(_first_defined(entry, ("__id", "id", "ID"))),
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


def normalized_clients(
    host_data: dict[str, Any],
    dhcp_data: dict[str, Any],
) -> list[dict[str, Any]]:
    """Return best-effort normalized LAN clients.

    Prefer DHCP StaticTbl (richer HostName/IP/MAC data), and merge runtime host
    attributes like active/interface when available.
    """
    host_clients = normalized_hosts(host_data)

    static_tbl = dhcp_data.get("StaticTbl", [])
    if not isinstance(static_tbl, list) or len(static_tbl) == 0:
        return host_clients

    static_clients = [
        normalize_host_entry(item, source_index=index)
        for index, item in enumerate(static_tbl)
        if isinstance(item, dict)
    ]

    host_by_mac = {
        str(client.get("mac_address")): client
        for client in host_clients
        if client.get("mac_address")
    }
    host_by_ip = {
        str(client.get("ip_address")): client
        for client in host_clients
        if client.get("ip_address")
    }

    merged: list[dict[str, Any]] = []
    for client in static_clients:
        mac = client.get("mac_address")
        ip = client.get("ip_address")
        host_match = None
        if mac and str(mac) in host_by_mac:
            host_match = host_by_mac[str(mac)]
        elif ip and str(ip) in host_by_ip:
            host_match = host_by_ip[str(ip)]

        if host_match:
            if host_match.get("active") is not None:
                client["active"] = host_match.get("active")
            if host_match.get("interface") and client.get("interface") == "unknown":
                client["interface"] = host_match.get("interface")
            if host_match.get("connection_type") and client.get("connection_type") == "unknown":
                client["connection_type"] = host_match.get("connection_type")

        merged.append(client)

    return sorted(
        merged,
        key=lambda x: (
            str(x.get("name") or "").lower(),
            str(x.get("ip_address") or ""),
            str(x.get("mac_address") or ""),
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
