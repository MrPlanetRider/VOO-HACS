#!/usr/bin/env python3
"""Debug VOO Gateway authentication - try with voo username."""

import asyncio
import sys
import json
import hashlib
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

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
    
    print("Testing with voo username for challenge")
    print("=" * 60)
    
    async with aiohttp.ClientSession() as session:
        try:
            # Step 1: Get challenge with 'voo' username
            print("\n[Step 1] Getting challenge with 'voo' username...")
            url = f"{base_url}/api/v1/session/login"
            data = {"username": "voo", "password": "seeksalthash"}
            
            async with session.post(
                url, 
                data=data, 
                timeout=aiohttp.ClientTimeout(10),
                headers=headers
            ) as r:
                response = await r.json()
                print(f"Status: {r.status}")
                print(f"Response: {json.dumps(response, indent=2)}")
                
                if response.get("error") != "ok":
                    print(f"✗ Challenge error")
                    return
                
                salt1 = response.get("salt")
                salt2 = response.get("saltwebui")
                print(f"\nSalts obtained: {salt1}, {salt2}")
            
            # Step 2: Compute PBKDF2 challenge
            print("\n[Step 2] Computing PBKDF2 challenge...")
            
            def pbkdf2_challenge(pwd: str, salt: str) -> str:
                bpass = pwd.encode("utf-8")
                bsalt = salt.encode("utf-8")
                digest = hashlib.pbkdf2_hmac("sha256", bpass, bsalt, 1000)
                return digest.hex()[:32]
            
            challenge = pbkdf2_challenge(password, salt1)
            challenge = pbkdf2_challenge(challenge, salt2)
            print(f"Challenge: {challenge}")
            
            # Step 3: Try with 'voo' username
            print("\n[Step 3a] Submitting with 'voo' username...")
            data = {"username": "voo", "password": challenge}
            
            async with session.post(
                url,
                data=data,
                timeout=aiohttp.ClientTimeout(10),
                headers=headers
            ) as r:
                response = await r.json()
                print(f"Status: {r.status}")
                print(f"Response: {json.dumps(response, indent=2)}")
                
                if response.get("error") == "ok":
                    print("✓ Authentication with 'voo' successful!")
                    return
            
            # Step 4: Try with 'user' username
            print("\n[Step 3b] Submitting with 'user' username...")
            data = {"username": "user", "password": challenge}
            
            async with session.post(
                url,
                data=data,
                timeout=aiohttp.ClientTimeout(10),
                headers=headers
            ) as r:
                response = await r.json()
                print(f"Status: {r.status}")
                print(f"Response: {json.dumps(response, indent=2)}")
                
                if response.get("error") == "ok":
                    print("✓ Authentication with 'user' successful!")
                    return
            
            print("\n✗ Both attempts failed")
        
        except Exception as e:
            import traceback
            print(f"✗ Error: {e}")
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_auth())
