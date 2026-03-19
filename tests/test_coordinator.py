"""Tests for VOO Gateway integration coordinator."""

import pytest
from unittest.mock import AsyncMock, MagicMock

from custom_components.voo_gateway.coordinator import VooGatewayDataUpdateCoordinator


@pytest.fixture
def mock_hass():
    """Create mock home assistant instance."""
    hass = MagicMock()
    hass.loop = MagicMock()
    return hass


@pytest.fixture
def mock_entry():
    """Create mock config entry."""
    entry = MagicMock()
    entry.data = {
        "host": "192.168.0.1",
        "username": "user",
        "password": "password123"
    }
    return entry


@pytest.mark.asyncio
async def test_coordinator_init(mock_hass, mock_entry):
    """Test coordinator initialization."""
    mock_api = MagicMock()
    coordinator = VooGatewayDataUpdateCoordinator(
        mock_hass,
        mock_entry,
        mock_api,
        scan_interval=300,
    )
    
    assert coordinator.api is mock_api


@pytest.mark.asyncio
async def test_coordinator_async_config_entry_first_refresh(mock_hass, mock_entry):
    """Test first refresh after config entry."""
    mock_api = AsyncMock()
    mock_api.get_system_info = AsyncMock(return_value={
        "ModelName": "CGA4233VOO",
        "FirmwareVersion": "V1.2.3.4",
        "Uptime": 86400
    })
    mock_api.get_dhcp_config = AsyncMock(return_value={
        "WANIPAddress": "203.0.113.1",
        "LANIPAddress": "192.168.0.1"
    })
    mock_api.get_connected_devices = AsyncMock(return_value={
        "hostTbl": [
            {"HostName": "device1"},
            {"HostName": "device2"}
        ]
    })
    mock_api.get_wifi_info = AsyncMock(return_value={})
    mock_api.get_modem_info = AsyncMock(return_value={
        "ModemStatus": "Online"
    })
    
    coordinator = VooGatewayDataUpdateCoordinator(
        mock_hass,
        mock_entry,
        mock_api,
        scan_interval=300,
    )
    
    data = await coordinator._async_update_data()
    
    assert data is not None
    assert "system" in data
    assert data["system"]["ModelName"] == "CGA4233VOO"
    assert len(data["host"]["hostTbl"]) == 2


@pytest.mark.asyncio
async def test_coordinator_update_error_handling(mock_hass, mock_entry):
    """Test coordinator handles update errors gracefully."""
    mock_api = AsyncMock()
    mock_api.get_system_info = AsyncMock(side_effect=Exception("API failed"))
    mock_api.get_dhcp_config = AsyncMock(return_value={})
    mock_api.get_connected_devices = AsyncMock(return_value={})
    mock_api.get_wifi_info = AsyncMock(return_value={})
    mock_api.get_modem_info = AsyncMock(return_value={})
    
    coordinator = VooGatewayDataUpdateCoordinator(
        mock_hass,
        mock_entry,
        mock_api,
        scan_interval=300,
    )
    
    # The coordinator should handle errors gracefully by returning data with empty dicts
    data = await coordinator._async_update_data()
    assert "system" in data
    assert data["system"] == {}  # Should be empty due to error


@pytest.mark.asyncio
async def test_coordinator_data_structure(mock_hass, mock_entry):
    """Test coordinator maintains expected data structure."""
    mock_api = AsyncMock()
    mock_api.get_system_info = AsyncMock(return_value={
        "ModelName": "CGA4233VOO",
        "FirmwareVersion": "V1.2.3.4",
        "Uptime": 86400
    })
    mock_api.get_dhcp_config = AsyncMock(return_value={
        "WANIPAddress": "203.0.113.1",
        "LANIPAddress": "192.168.0.1",
        "SubnetMask": "255.255.255.0"
    })
    mock_api.get_connected_devices = AsyncMock(return_value={
        "hostTbl": [
            {"HostName": "device1", "IPAddress": "192.168.0.10"},
            {"HostName": "device2", "IPAddress": "192.168.0.11"}
        ]
    })
    mock_api.get_wifi_info = AsyncMock(return_value={})
    mock_api.get_modem_info = AsyncMock(return_value={
        "ModemStatus": "Online"
    })
    
    coordinator = VooGatewayDataUpdateCoordinator(
        mock_hass,
        mock_entry,
        mock_api,
        scan_interval=300,
    )
    
    data = await coordinator._async_update_data()
    
    # Verify data structure
    assert "system" in data
    assert "dhcp" in data
    assert "host" in data
    assert "wifi" in data
    assert "modem" in data
    assert len(data["host"]["hostTbl"]) == 2
