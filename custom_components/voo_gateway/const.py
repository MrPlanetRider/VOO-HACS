"""Constants for the VOO Gateway integration."""

from typing import Final

DOMAIN: Final = "voo_gateway"

CONF_SCAN_INTERVAL: Final = "scan_interval"

DEFAULT_SCAN_INTERVAL: Final = 300
DEFAULT_HOST: Final = "192.168.0.1"

# API endpoints
API_BASE: Final = "/api/v1"
API_SESSION_LOGIN: Final = f"{API_BASE}/session/login"
API_SESSION_MENU: Final = f"{API_BASE}/session/menu"
API_SYSTEM: Final = f"{API_BASE}/system"
API_DHCP: Final = f"{API_BASE}/dhcp/v4/1"
API_HOST: Final = f"{API_BASE}/host"
API_MODEM: Final = f"{API_BASE}/modem"
API_WIFI: Final = f"{API_BASE}/wifi"

# System info fields
SYSTEM_FIELDS: Final = [
    "HardwareVersion",
    "FirmwareName",
    "CMMACAddress",
    "MACAddressRT",
    "UpTime",
    "LocalTime",
    "LanMode",
    "ModelName",
    "CMStatus",
    "Manufacturer",
    "SerialNumber",
    "SoftwareVersion",
    "BootloaderVersion",
    "ProcessorSpeed",
    "MemTotal",
    "MemFree",
]

# DHCP fields
DHCP_FIELDS: Final = [
    "IPAddressRT",
    "SubnetMaskRT",
    "IPAddressGW",
    "DNSTblRT",
    "PoolEnable",
    "WanAddressMode",
    "LanIPAddress",
    "LanSubnetMask",
]

# Host fields
HOST_FIELDS: Final = [
    "hostTbl",
    "LanMode",
    "MixedMode",
    "LanPortMode",
]
