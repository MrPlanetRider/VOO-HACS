#!/usr/bin/env python3
"""Debug VOO Gateway authentication."""

import asyncio
import sys
import json
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import aiohttp directly
import aiohttp

async def debug_auth():
    """Debug authentication process."""
    
    host = "192.168.0.1"
    username = "voo"
    password = "PsxpBE2KHVjE"
    
    base_url = f"http://{host}"
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
        "X-Requested-With": "XMLHttpRequest",
    }
    
    print("Debugging VOO Gateway Authentication")
    print("=" * 60)
    print(f"Host: {host}")
    print(f"Username: {username}")
    print(f"Password: {'*' * len(password)}")
    print("=" * 60)
    
    async with aiohttp.ClientSession() as session:
        try:
            # Step 1: Get challenge
            print("\n[Step 1] Getting challenge/salt from server...")
            url = f"{base_url}/api/v1/session/login"
            data = {"username": username, "password": "seeksalthash"}
            
            print(f"POST {url}")
            print(f"Data: {data}")
            
            async with session.post(
                url, 
                data=data, 
                timeout=aiohttp.ClientTimeout(10),
                headers=headers
            ) as r:
                response = await r.json()
                print(f"Status: {r.status}")
                print(f"Response: {json.dumps(response, indent=2)}")
                
                if r.status != 200:
                    print(f"✗ Failed to get challenge: HTTP {r.status}")
                    return
                
                if response.get("error") != "ok":
                    print(f"✗ Challenge error: {response.get('error')}")
                    return
                
                salt1 = response.get("salt")
                salt2 = response.get("saltwebui")
                
                print(f"\nsalt: {salt1}")
                print(f"saltwebui: {salt2}")
                
                if not salt1 or not salt2:
                    print("✗ Missing salt in response")
                    return
            
            # Step 2: Compute PBKDF2 challenge
            print("\n[Step 2] Computing PBKDF2 challenge...")
            import hashlib
            
            def pbkdf2_challenge(pwd: str, salt: str) -> str:
                bpass = pwd.encode("utf-8")
                bsalt = salt.encode("utf-8")
                digest = hashlib.pbkdf2_hmac("sha256", bpass, bsalt, 1000)
                return digest.hex()[:32]
            
            challenge = pbkdf2_challenge(password, salt1)
            print(f"After first PBKDF2: {challenge}")
            
            challenge = pbkdf2_challenge(challenge, salt2)
            print(f"After second PBKDF2: {challenge}")
            
            # Step 3: Submit authentication
            print("\n[Step 3] Submitting authentication...")
            data = {"username": "user", "password": challenge}
            
            print(f"POST {url}")
            print(f"Data: {data}")
            
            async with session.post(
                url,
                data=data,
                timeout=aiohttp.ClientTimeout(10),
                headers=headers
            ) as r:
                response = await r.json()
                print(f"Status: {r.status}")
                print(f"Response: {json.dumps(response, indent=2)}")
                
                if r.status != 200:
                    print(f"✗ Failed to authenticate: HTTP {r.status}")
                    return
                
                if response.get("error") != "ok":
                    print(f"✗ Authentication failed: {response.get('error')}")
                    # Print full response to debug
                    print(f"Full response: {response}")
                    return
                
                print("✓ Authentication successful!")
                
                # Check cookies
                print("\nCookies:")
                for cookie_name, cookie in session.cookie_jar.items():
                    print(f"  {cookie_name}: {cookie}")
        
        except aiohttp.ClientError as e:
            print(f"✗ Connection error: {e}")
        except json.JSONDecodeError as e:
            print(f"✗ JSON decode error: {e}")
        except Exception as e:
            import traceback
            print(f"✗ Unexpected error: {e}")
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_auth())
