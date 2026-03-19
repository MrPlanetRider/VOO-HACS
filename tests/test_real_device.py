#!/usr/bin/env python3
"""Test real VOO Gateway device integration."""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import the API client directly
import importlib.util
voo_api_path = project_root / "custom_components" / "voo_gateway" / "voo_api.py"
spec = importlib.util.spec_from_file_location("voo_api", voo_api_path)
voo_api_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(voo_api_module)

VooApi = voo_api_module.VooApi
VooAuthError = voo_api_module.VooAuthError
VooApiError = voo_api_module.VooApiError

async def test_real_device():
    """Test connection and API calls against real device."""
    
    # Device credentials
    host = "192.168.0.1"
    username = "voo"
    password = "PsxpBE2KHVjE"
    
    print(f"Testing VOO Gateway at {host}")
    print("=" * 60)
    
    # Initialize API client
    api = VooApi(host, username, password, timeout=10)
    
    try:
        # Test 1: Authentication
        print("\n[1/6] Testing authentication...")
        await api.authenticate()
        print("✓ Authentication successful")
        
        # Test 2: System info
        print("\n[2/6] Fetching system information...")
        system_info = await api.get_system_info()
        print(f"✓ System info retrieved:")
        for key, value in system_info.items():
            print(f"  - {key}: {value}")
        
        # Test 3: DHCP config
        print("\n[3/6] Fetching DHCP configuration...")
        dhcp_info = await api.get_dhcp_config()
        print(f"✓ DHCP config retrieved:")
        for key, value in dhcp_info.items():
            print(f"  - {key}: {value}")
        
        # Test 4: Connected devices
        print("\n[4/6] Fetching connected devices...")
        devices_info = await api.get_connected_devices()
        if "hostTbl" in devices_info:
            print(f"✓ Found {len(devices_info['hostTbl'])} connected device(s):")
            for device in devices_info["hostTbl"]:
                host_name = device.get("HostName", "Unknown")
                ip_addr = device.get("IPAddress", "N/A")
                print(f"  - {host_name} ({ip_addr})")
        else:
            print("✓ No devices found or empty device list")
        
        # Test 5: WiFi info
        print("\n[5/6] Fetching WiFi information...")
        wifi_info = await api.get_wifi_info()
        if wifi_info:
            print(f"✓ WiFi info retrieved:")
            for key, value in wifi_info.items():
                print(f"  - {key}: {value}")
        else:
            print("✓ WiFi info (empty or not available)")
        
        # Test 6: Modem info
        print("\n[6/6] Fetching modem information...")
        modem_info = await api.get_modem_info()
        print(f"✓ Modem info retrieved:")
        for key, value in modem_info.items():
            print(f"  - {key}: {value}")
        
        print("\n" + "=" * 60)
        print("✓ All tests passed!")
        print("=" * 60)
        
        return True
        
    except VooAuthError as e:
        print(f"\n✗ Authentication error: {e}")
        return False
    except VooApiError as e:
        print(f"\n✗ API error: {e}")
        return False
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        await api.close()

async def main():
    """Main entry point."""
    success = await test_real_device()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    asyncio.run(main())
