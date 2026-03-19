"""Tests for VOO Gateway API client."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import aiohttp

from custom_components.voo_gateway.voo_api import VooApi, VooAuthError, VooApiError


class TestVooApiAuthentication:
    """Test authentication flow."""

    @pytest.mark.asyncio
    async def test_pbkdf2_challenge(self):
        """Test PBKDF2 challenge computation."""
        api = VooApi("192.168.0.1", "user", "password123")
        
        # Test with known values
        challenge = api._pbkdf2_challenge("password123", "testsalt")
        
        # Should return 32 character hex string
        assert len(challenge) == 32
        assert all(c in "0123456789abcdef" for c in challenge)

    @pytest.mark.asyncio
    async def test_authenticate_success(self):
        """Test successful authentication."""
        api = VooApi("192.168.0.1", "user", "password123")
        
        # Mock the session
        mock_session = AsyncMock()
        api.session = mock_session
        
        # First response: challenge salts
        challenge_response = MagicMock()
        challenge_response.status = 200
        challenge_response.json = AsyncMock(return_value={
            "error": "ok",
            "salt": "saltsalt123",
            "saltwebui": "webui456"
        })
        
        # Second response: successful auth
        auth_response = MagicMock()
        auth_response.status = 200
        auth_response.json = AsyncMock(return_value={
            "error": "ok",
            "sessionid": "abc123"
        })
        
        # Mock context manager
        challenge_cm = MagicMock()
        challenge_cm.__aenter__ = AsyncMock(return_value=challenge_response)
        challenge_cm.__aexit__ = AsyncMock(return_value=None)
        
        auth_cm = MagicMock()
        auth_cm.__aenter__ = AsyncMock(return_value=auth_response)
        auth_cm.__aexit__ = AsyncMock(return_value=None)
        
        # Set up side effects for POST calls
        post_responses = [challenge_cm, auth_cm]
        mock_session.post = MagicMock(side_effect=post_responses)
        
        # Mock cookie jar
        mock_cookie = MagicMock()
        mock_cookie.value = "csrf_token_123"
        mock_session.cookie_jar.get = MagicMock(return_value=mock_cookie)
        
        await api.authenticate()
        
        # Verify CSRF token was set
        assert api._headers["X-CSRF-TOKEN"] == "csrf_token_123"

    @pytest.mark.asyncio
    async def test_authenticate_missing_salt(self):
        """Test authentication fails when salt is missing."""
        api = VooApi("192.168.0.1", "user", "password123")
        
        mock_session = AsyncMock()
        api.session = mock_session
        
        # Response missing salt
        response = MagicMock()
        response.status = 200
        response.json = AsyncMock(return_value={
            "error": "ok",
            "salt": None,
            "saltwebui": "webui456"
        })
        
        cm = MagicMock()
        cm.__aenter__ = AsyncMock(return_value=response)
        cm.__aexit__ = AsyncMock(return_value=None)
        
        mock_session.post = MagicMock(return_value=cm)
        
        with pytest.raises(VooAuthError, match="Missing salt"):
            await api.authenticate()

    @pytest.mark.asyncio
    async def test_authenticate_connection_error(self):
        """Test authentication handles connection errors."""
        api = VooApi("192.168.0.1", "user", "password123")
        
        mock_session = AsyncMock()
        api.session = mock_session
        
        mock_session.post = MagicMock(
            side_effect=aiohttp.ClientError("Connection failed")
        )
        
        with pytest.raises(VooApiError, match="Connection error"):
            await api.authenticate()


class TestVooApiRequests:
    """Test API request methods."""

    @pytest.mark.asyncio
    async def test_get_system_info(self):
        """Test getting system information."""
        api = VooApi("192.168.0.1", "user", "password123")
        
        mock_session = AsyncMock()
        api.session = mock_session
        
        response = MagicMock()
        response.status = 200
        response.json = AsyncMock(return_value={
            "error": "ok",
            "data": {
                "ModelName": "CGA4233VOO",
                "HardwareVersion": "C0A4233VOO",
                "FirmwareVersion": "V1.2.3.4"
            }
        })
        
        cm = MagicMock()
        cm.__aenter__ = AsyncMock(return_value=response)
        cm.__aexit__ = AsyncMock(return_value=None)
        
        mock_session.get = MagicMock(return_value=cm)
        
        result = await api.get_system_info(["ModelName", "HardwareVersion"])
        
        assert result["ModelName"] == "CGA4233VOO"
        assert result["HardwareVersion"] == "C0A4233VOO"

    @pytest.mark.asyncio
    async def test_get_connected_devices(self):
        """Test getting connected devices."""
        api = VooApi("192.168.0.1", "user", "password123")
        
        mock_session = AsyncMock()
        api.session = mock_session
        
        response = MagicMock()
        response.status = 200
        response.json = AsyncMock(return_value={
            "error": "ok",
            "data": {
                "hostTbl": [
                    {"HostName": "device1", "IPAddress": "192.168.0.10"},
                    {"HostName": "device2", "IPAddress": "192.168.0.11"}
                ]
            }
        })
        
        cm = MagicMock()
        cm.__aenter__ = AsyncMock(return_value=response)
        cm.__aexit__ = AsyncMock(return_value=None)
        
        mock_session.get = MagicMock(return_value=cm)
        
        result = await api.get_connected_devices()
        
        assert len(result["hostTbl"]) == 2
        assert result["hostTbl"][0]["HostName"] == "device1"

    @pytest.mark.asyncio
    async def test_get_modem_info(self):
        """Test getting modem information."""
        api = VooApi("192.168.0.1", "user", "password123")
        
        mock_session = AsyncMock()
        api.session = mock_session
        
        response = MagicMock()
        response.status = 200
        response.json = AsyncMock(return_value={
            "error": "ok",
            "data": {
                "ModemStatus": "Online",
                "DownstreamPower": "10.5 dBmV"
            }
        })
        
        cm = MagicMock()
        cm.__aenter__ = AsyncMock(return_value=response)
        cm.__aexit__ = AsyncMock(return_value=None)
        
        mock_session.get = MagicMock(return_value=cm)
        
        result = await api.get_modem_info()
        
        assert result["ModemStatus"] == "Online"

    @pytest.mark.asyncio
    async def test_not_authenticated(self):
        """Test request fails when not authenticated."""
        api = VooApi("192.168.0.1", "user", "password123")
        api.session = None
        
        with pytest.raises(VooApiError, match="Not authenticated"):
            await api.get_system_info()

    @pytest.mark.asyncio
    async def test_api_error_response(self):
        """Test handling of API error responses."""
        api = VooApi("192.168.0.1", "user", "password123")
        
        mock_session = AsyncMock()
        api.session = mock_session
        
        response = MagicMock()
        response.status = 200
        response.json = AsyncMock(return_value={
            "error": "unauthorized"
        })
        
        cm = MagicMock()
        cm.__aenter__ = AsyncMock(return_value=response)
        cm.__aexit__ = AsyncMock(return_value=None)
        
        mock_session.get = MagicMock(return_value=cm)
        
        with pytest.raises(VooApiError, match="unauthorized"):
            await api.get_system_info()

    @pytest.mark.asyncio
    async def test_close_session(self):
        """Test closing session."""
        api = VooApi("192.168.0.1", "user", "password123")
        
        mock_session = AsyncMock()
        api.session = mock_session
        
        await api.close()
        
        mock_session.close.assert_called_once()
        assert api.session is None


class TestEndpointBuilding:
    """Test endpoint URL building."""

    def test_build_endpoint_no_fields(self):
        """Test building endpoint without fields."""
        api = VooApi("192.168.0.1", "user", "password123")
        
        endpoint = api._build_endpoint("system")
        
        assert endpoint.startswith("/api/v1/system?_=")
        assert "?_=" in endpoint

    def test_build_endpoint_with_fields(self):
        """Test building endpoint with fields."""
        api = VooApi("192.168.0.1", "user", "password123")
        
        endpoint = api._build_endpoint("system", ["ModelName", "FirmwareVersion"])
        
        assert "/api/v1/system/ModelName,FirmwareVersion?_=" in endpoint

    def test_build_endpoint_empty_fields(self):
        """Test building endpoint with empty fields list."""
        api = VooApi("192.168.0.1", "user", "password123")
        
        endpoint = api._build_endpoint("system", [])
        
        assert endpoint.startswith("/api/v1/system?_=")
