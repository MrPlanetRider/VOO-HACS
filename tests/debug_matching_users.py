#!/usr/bin/env python3
"""Debug - test with matching usernames"""

import asyncio
import sys
import json
import hashlib
from pathlib import Path

import aiohttp

async def test_matching_users():
    """Test authentication with matching usernames in challenge and login."""
    
    host = "192.168.0.1"
    username = "voo"
    password = "PsxpBE2KHVjE"
    
    base_url = f"http://{host}"
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
        "X-Requested-With": "XMLHttpRequest",
    }
    
    print("Testing with matching username 'voo' in both steps")
    print("=" * 60)
    
    async with aiohttp.ClientSession() as session:
        try:
            # Step 1: Get challenge with 'voo' username
            print("\n[Step 1] Getting challenge with 'voo'...")
            url = f"{base_url}/api/v1/session/login"
            data = {"username": "voo", "password": "seeksalthash"}
            
            async with session.post(
                url, 
                data=data, 
                timeout=aiohttp.ClientTimeout(10),
                headers=headers
            ) as r:
                response = await r.json()
                if response.get("error") != "ok":
                    print(f"✗ Challenge failed: {response}")
                    return
                salt1 = response.get("salt")
                salt2 = response.get("saltwebui")
                print(f"✓ Got salts: {salt1}, {salt2}")
            
            # Step 2: Compute PBKDF2
            def pbkdf2_challenge(pwd: str, salt: str) -> str:
                bpass = pwd.encode("utf-8")
                bsalt = salt.encode("utf-8")
                digest = hashlib.pbkdf2_hmac("sha256", bpass, bsalt, 1000)
                return digest.hex()[:32]
            
            challenge = pbkdf2_challenge(password, salt1)
            challenge = pbkdf2_challenge(challenge, salt2)
            print(f"\n[Step 2] Challenge computed: {challenge}")
            
            # Step 3: Login with 'voo' username (matching)
            print("\n[Step 3] Submitting login with 'voo' username...")
            data = {"username": "voo", "password": challenge}
            
            async with session.post(
                url,
                data=data,
                timeout=aiohttp.ClientTimeout(10),
                headers=headers
            ) as r:
                response = await r.json()
                print(f"Response: {json.dumps(response, indent=2)}")
                
                if response.get("error") == "ok":
                    print("\n✓ SUCCESS! Authentication with 'voo' username works!")
                    print(f"Session info: {response.get('sessionid', 'N/A')}")
                    
                    # Check cookies
                    print("\nCookies obtained:")
                    for name, cookie in session.cookie_jar.items():
                        print(f"  {name}: {cookie.value}")
                    return True
                else:
                    print(f"\n✗ Login failed: {response.get('message', response.get('error'))}")
                    return False
        
        except Exception as e:
            import traceback
            print(f"✗ Error: {e}")
            traceback.print_exc()
            return False

if __name__ == "__main__":
    success = asyncio.run(test_matching_users())
    sys.exit(0 if success else 1)
