"""Constants for the VOO Router (Technicolor CGA4233) integration."""
from __future__ import annotations

from typing import Final

DOMAIN: Final = "voo_router"

CONF_SCAN_INTERVAL: Final = "scan_interval"

DEFAULT_HOST: Final = "192.168.0.1"
DEFAULT_USERNAME: Final = "voo"
DEFAULT_SCAN_INTERVAL: Final = 60

ATTR_MANUFACTURER: Final = "Technicolor"
