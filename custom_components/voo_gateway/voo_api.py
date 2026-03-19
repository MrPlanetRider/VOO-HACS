"""VOO Gateway API client."""

import hashlib
import time
import logging
from typing import Any, Dict

import aiohttp

_LOGGER = logging.getLogger(__name__)


class VooAuthError(Exception):
    """Authentication error."""

    pass


class VooApiError(Exception):
    """API error."""

    pass


class VooApi:
    """VOO Gateway API client with PBKDF2 challenge authentication."""

    def __init__(
        self,
        host: str,
        username: str,
        password: str,
        timeout: int = 10,
    ):
        """Initialize API client.

        Args:
            host: Router IP address (e.g. 192.168.0.1)
            username: Username for router login
            password: Password for router login
            timeout: Request timeout in seconds
        """
        self.host = host
        self.username = username
        self.password = password
        self.timeout = timeout
        self.base_url = f"http://{host}"
        self.session: aiohttp.ClientSession | None = None
        self._headers = {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
            "X-Requested-With": "XMLHttpRequest",
        }

    async def authenticate(self) -> None:
        """Authenticate with the router using 2-step PBKDF2 challenge."""
        if self.session is None:
            self.session = aiohttp.ClientSession()

        try:
            # Step 1: Get challenge salt
            url = f"{self.base_url}/api/v1/session/login"
            data = {"username": self.username, "password": "seeksalthash"}

            async with self.session.post(
                url, data=data, timeout=aiohttp.ClientTimeout(self.timeout), headers=self._headers
            ) as r:
                if r.status != 200:
                    raise VooAuthError(f"Failed to get challenge: HTTP {r.status}")
                response = await r.json()

            if response.get("error") != "ok":
                raise VooAuthError(f"Challenge error: {response.get('error')}")

            salt1 = response.get("salt")
            salt2 = response.get("saltwebui")

            if not salt1 or not salt2:
                raise VooAuthError("Missing salt in challenge response")

            # Step 2: Compute PBKDF2 challenge
            challenge = self._pbkdf2_challenge(self.password, salt1)
            challenge = self._pbkdf2_challenge(challenge, salt2)

            # Step 3: Submit challenge response
            data = {"username": "user", "password": challenge}

            async with self.session.post(
                url, data=data, timeout=aiohttp.ClientTimeout(self.timeout), headers=self._headers
            ) as r:
                if r.status != 200:
                    raise VooAuthError(f"Failed to authenticate: HTTP {r.status}")
                response = await r.json()

            if response.get("error") != "ok":
                raise VooAuthError(f"Authentication failed: {response.get('error')}")

            # Extract CSRF token from auth cookie
            auth_cookie = self.session.cookie_jar.get("auth")
            if auth_cookie:
                self._headers["X-CSRF-TOKEN"] = auth_cookie.value

            _LOGGER.debug("Successfully authenticated with VOO Gateway")

        except aiohttp.ClientError as e:
            raise VooApiError(f"Connection error: {e}")

    @staticmethod
    def _pbkdf2_challenge(password: str, salt: str) -> str:
        """Compute PBKDF2-SHA256 challenge hash.

        Args:
            password: Password or intermediate hash
            salt: Salt value

        Returns:
            First 32 chars of hex digest
        """
        bpass = password.encode("utf-8")
        bsalt = salt.encode("utf-8")
        digest = hashlib.pbkdf2_hmac("sha256", bpass, bsalt, 1000)
        return digest.hex()[:32]

    async def _make_request(
        self, endpoint: str, params: Dict[str, Any] | None = None
    ) -> Dict[str, Any]:
        """Make an API request.

        Args:
            endpoint: API endpoint path (e.g. "/api/v1/system/ModelName")
            params: Query parameters

        Returns:
            Response data dict

        Raises:
            VooApiError: If request fails
        """
        if self.session is None:
            raise VooApiError("Not authenticated")

        url = f"{self.base_url}{endpoint}"

        try:
            async with self.session.get(
                url,
                params=params,
                timeout=aiohttp.ClientTimeout(self.timeout),
                headers=self._headers,
            ) as r:
                if r.status != 200:
                    raise VooApiError(f"HTTP {r.status}")

                response = await r.json()

                if response.get("error") != "ok":
                    raise VooApiError(f"API error: {response.get('error')}")

                return response.get("data", {})

        except aiohttp.ClientError as e:
            raise VooApiError(f"Request failed: {e}")

    def _build_endpoint(self, target: str, fields: list[str] | None = None) -> str:
        """Build API endpoint URL with fields.

        Args:
            target: Target path (e.g. "system")
            fields: Optional list of field names to request

        Returns:
            Full endpoint path
        """
        now = int(time.time() * 1000)

        if not fields or len(fields) == 0:
            return f"/api/v1/{target}?_={now}"

        field_str = ",".join(fields)
        return f"/api/v1/{target}/{field_str}?_={now}"

    async def get_system_info(self, fields: list[str] | None = None) -> Dict[str, Any]:
        """Get system information.

        Args:
            fields: List of system fields to fetch

        Returns:
            System info dict
        """
        endpoint = self._build_endpoint("system", fields)
        return await self._make_request(endpoint)

    async def get_dhcp_config(self, fields: list[str] | None = None) -> Dict[str, Any]:
        """Get DHCP configuration.

        Args:
            fields: List of DHCP fields to fetch

        Returns:
            DHCP config dict
        """
        endpoint = self._build_endpoint("dhcp/v4/1", fields)
        return await self._make_request(endpoint)

    async def get_connected_devices(self, fields: list[str] | None = None) -> Dict[str, Any]:
        """Get connected devices list.

        Args:
            fields: List of host fields to fetch

        Returns:
            Host info dict with hostTbl
        """
        endpoint = self._build_endpoint("host", fields)
        return await self._make_request(endpoint)

    async def get_wifi_info(self, fields: list[str] | None = None) -> Dict[str, Any]:
        """Get WiFi information.

        Args:
            fields: List of WiFi fields to fetch

        Returns:
            WiFi info dict
        """
        endpoint = self._build_endpoint("wifi", fields)
        return await self._make_request(endpoint)

    async def get_modem_info(self, fields: list[str] | None = None) -> Dict[str, Any]:
        """Get modem information.

        Args:
            fields: List of modem fields to fetch

        Returns:
            Modem info dict
        """
        endpoint = self._build_endpoint("modem", fields)
        return await self._make_request(endpoint)

    async def close(self) -> None:
        """Close session."""
        if self.session:
            await self.session.close()
            self.session = None
