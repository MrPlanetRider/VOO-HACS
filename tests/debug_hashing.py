#!/usr/bin/env python3
"""Debug - test different hashing approaches"""

import asyncio
import sys
import json
import hashlib

import aiohttp

async def test_hashing_approaches():
    """Test different password hashing approaches."""
    
    host = "192.168.0.1"
    username = "voo"
    password = "PsxpBE2KHVjE"
    
    base_url = f"http://{host}"
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
        "X-Requested-With": "XMLHttpRequest",
    }
    
    print("Testing different hashing approaches")
    print("=" * 60)
    
    # Get challenge
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
            salt1 = response.get("salt")
            salt2 = response.get("saltwebui")
            print(f"✓ Salts: salt1={salt1}, salt2={salt2}")
    
    def pbkdf2(pwd: str, salt: str, iters: int = 1000) -> str:
        bpass = pwd.encode("utf-8")
        bsalt = salt.encode("utf-8")
        digest = hashlib.pbkdf2_hmac("sha256", bpass, bsalt, iters)
        return digest.hex()
    
    # Test different hashing approaches
    approaches = [
        ("Raw password", lambda: password),
        ("Salt1 only (hex[:32])", lambda: pbkdf2(password, salt1)[:32]),
        ("Salt1 only (full hex)", lambda: pbkdf2(password, salt1)),
        ("Salt2 only (hex[:32])", lambda: pbkdf2(password, salt2)[:32]),
        ("Salt2 only (full hex)", lambda: pbkdf2(password, salt2)),
        ("Salt1 then Salt2 (hex[:32])", lambda: pbkdf2(pbkdf2(password, salt1), salt2)[:32]),
        ("Salt1 then Salt2 (full hex)", lambda: pbkdf2(pbkdf2(password, salt1), salt2)),
        ("Salt2 then Salt1 (hex[:32])", lambda: pbkdf2(pbkdf2(password, salt2), salt1)[:32]),
        ("Salt2 then Salt1 (full hex)", lambda: pbkdf2(pbkdf2(password, salt2), salt1)),
        ("Just salt1 with user in password", lambda: pbkdf2(f"{username}{password}", salt1)[:32]),
        ("MD5(password)", lambda: hashlib.md5(password.encode()).hexdigest()),
        ("SHA256(password)", lambda: hashlib.sha256(password.encode()).hexdigest()),
    ]
    
    url = f"{base_url}/api/v1/session/login"
    
    for description, hash_func in approaches:
        print(f"\n[{description}]")
        try:
            pwd_hash = hash_func()
            print(f"  Hash: {pwd_hash[:40]}...")
            
            async with aiohttp.ClientSession() as session:
                data = {"username": "voo", "password": pwd_hash}
                
                async with session.post(
                    url,
                    data=data,
                    timeout=aiohttp.ClientTimeout(10),
                    headers=headers
                ) as r:
                    response = await r.json()
                    
                    if response.get("error") == "ok":
                        print(f"  ✓✓✓ SUCCESS!")
                        print(f"  Full response: {json.dumps(response, indent=2)}")
                        return True
                    else:
                        result = response.get("message", response.get("error"))
                        print(f"  ✗ {result}")
        except Exception as e:
            print(f"  ✗ Error: {e}")
    
    print("\n✗ None of the approaches worked")
    return False

if __name__ == "__main__":
    success = asyncio.run(test_hashing_approaches())
    sys.exit(0 if success else 1)
