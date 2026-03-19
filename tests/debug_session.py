#!/usr/bin/env python3
"""Debug - check cookies and session handling"""

import asyncio
import sys
import json
import hashlib
import time

import aiohttp

async def test_session_handling():
    """Test with proper session handling and cookies."""
    
    host = "192.168.0.1"  
    username = "voo"
    password = "PsxpBE2KHVjE"
    
    base_url = f"http://{host}"
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
        "X-Requested-With": "XMLHttpRequest",
    }
    
    print("Testing session and cookie handling")
    print("=" * 60)
    
    # Use single session for both requests
    async with aiohttp.ClientSession() as session:
        try:
            url = f"{base_url}/api/v1/session/login"
            
            # Step 1: Challenge
            print("\n[Step 1] Getting challenge...")
            data = {"username": "voo", "password": "seeksalthash"}
            
            async with session.post(
                url, 
                data=data, 
                timeout=aiohttp.ClientTimeout(10),
                headers=headers
            ) as r:
                response = await r.json()
                print(f"  Status: {r.status}")
                print(f"  Response: {json.dumps(response, indent=2) if response else 'empty'}")
                
                # Check cookies
                print(f"  Cookies after challenge:")
                all_cookies = session.cookie_jar
                if all_cookies:
                    for cookie in all_cookies:
                        print(f"    {cookie.key}: {cookie.value}")
                else:
                    print(f"    (none)")
                
                salt1 = response.get("salt")
                salt2 = response.get("saltwebui")
                if not (salt1 and salt2):
                    print("  ✗ Missing salts")
                    return
            
            # Step 2: Compute hash
            def pbkdf2(pwd: str, salt: str) -> str:
                bpass = pwd.encode("utf-8")
                bsalt = salt.encode("utf-8")
                digest = hashlib.pbkdf2_hmac("sha256", bpass, bsalt, 1000)
                return digest.hex()[:32]
            
            challenge = pbkdf2(password, salt1)
            challenge = pbkdf2(challenge, salt2)
            print(f"\n[Step 2] Challenge: {challenge}")
            
            # Step 3: Wait a bit (in case timing matters)
            print("\n[Step 3] Waiting 1 second...")
            await asyncio.sleep(1)
            
            # Step 4: Login
            print("\n[Step 4] Submitting login...")
            print(f"  Headers: {headers}")
            
            data = {"username": "voo", "password": challenge}
            print(f"  Data: {data}")
            
            async with session.post(
                url,
                data=data,
                timeout=aiohttp.ClientTimeout(10),
                headers=headers
            ) as r:
                response = await r.json()
                print(f"  Status: {r.status}")
                print(f"  Response: {json.dumps(response, indent=2)}")
                
                # Check cookies again
                print(f"  Cookies after login:")
                all_cookies = session.cookie_jar
                if all_cookies:
                    for cookie in all_cookies:
                        print(f"    {cookie.key}: {cookie.value}")
                else:
                    print(f"    (none)")
                
                if response.get("error") == "ok":
                    print("\n✓ SUCCESS!")
                    return True
                else:
                    print(f"\n✗ Failed: {response.get('message', response.get('error'))}")
                    return False
        
        except Exception as e:
            import traceback
            print(f"✗ Error: {e}")
            traceback.print_exc()
            return False

if __name__ == "__main__":
    success = asyncio.run(test_session_handling())
    sys.exit(0 if success else 1)
