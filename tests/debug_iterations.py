#!/usr/bin/env python3
"""Debug - test with different PBKDF2 iterations"""

import asyncio
import sys
import json
import hashlib
from pathlib import Path

import aiohttp

async def test_pbkdf2_iterations():
    """Test authentication with different PBKDF2 iteration counts."""
    
    host = "192.168.0.1"
    username = "voo"
    password = "PsxpBE2KHVjE"
    
    base_url = f"http://{host}"
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
        "X-Requested-With": "XMLHttpRequest",
    }
    
    print("Testing different PBKDF2 iteration counts")
    print("=" * 60)
    
    # Get challenge once
    async with aiohttp.ClientSession() as session_challenge:
        print("\n[Getting challenge...]")
        url = f"{base_url}/api/v1/session/login"
        data = {"username": "voo", "password": "seeksalthash"}
        
        async with session_challenge.post(
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
    
    # Try different iteration counts
    iterations_to_try = [1, 10, 100, 500, 1000, 2000, 5000, 10000]
    
    for iterations in iterations_to_try:
        print(f"\n[Testing with {iterations} iterations...]")
        
        def pbkdf2_challenge(pwd: str, salt: str, iters: int) -> str:
            bpass = pwd.encode("utf-8")
            bsalt = salt.encode("utf-8")
            digest = hashlib.pbkdf2_hmac("sha256", bpass, bsalt, iters)
            return digest.hex()[:32]
        
        challenge = pbkdf2_challenge(password, salt1, iterations)
        challenge = pbkdf2_challenge(challenge, salt2, iterations)
        
        async with aiohttp.ClientSession() as session:
            try:
                data = {"username": "voo", "password": challenge}
                
                async with session.post(
                    url,
                    data=data,
                    timeout=aiohttp.ClientTimeout(10),
                    headers=headers
                ) as r:
                    response = await r.json()
                    
                    if response.get("error") == "ok":
                        print(f"✓✓✓ SUCCESS with {iterations} iterations!")
                        print(f"Response: {json.dumps(response, indent=2)}")
                        return True
                    else:
                        result = response.get("message", response.get("error"))
                        print(f"  ✗ {result}")
            except Exception as e:
                print(f"  ✗ Error: {e}")
    
    print("\n✗ None of the iteration counts worked")
    return False

if __name__ == "__main__":
    success = asyncio.run(test_pbkdf2_iterations())
    sys.exit(0 if success else 1)
