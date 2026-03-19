#!/usr/bin/env python3
"""Debug - test different request formats"""

import asyncio
import sys
import json
import hashlib

import aiohttp

async def test_request_formats():
    """Test different request formats for authentication."""
    
    host = "192.168.0.1"
    username = "voo"
    password = "PsxpBE2KHVjE"
    
    base_url = f"http://{host}"
    headers_base = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
        "X-Requested-With": "XMLHttpRequest",
    }
    
    print("Testing different request formats")
    print("=" * 60)
    
    # Get challenge using form data
    async with aiohttp.ClientSession() as session:
        url = f"{base_url}/api/v1/session/login"
        data = {"username": "voo", "password": "seeksalthash"}
        
        async with session.post(url, data=data, headers=headers_base) as r:
            response = await r.json()
            salt1 = response.get("salt")
            salt2 = response.get("saltwebui")
            print(f"✓ Challenge obtained: salt1={salt1}, salt2={salt2}")
    
    # Compute hash
    def pbkdf2(pwd: str, salt: str) -> str:
        bpass = pwd.encode("utf-8")
        bsalt = salt.encode("utf-8")
        digest = hashlib.pbkdf2_hmac("sha256", bpass, bsalt, 1000)
        return digest.hex()[:32]
    
    challenge = pbkdf2(password, salt1)
    challenge = pbkdf2(challenge, salt2)
    print(f"\n✓ Challenge computed: {challenge}")
    
    # Test different formats
    test_cases = [
        ("Form data (current)", "form", None),
        ("JSON with Content-Type", "json", "application/json"),
        ("JSON without Content-Type", "json_no_ct", "application/json"),
        ("x-www-form-urlencoded", "form_explicit", None),
    ]
    
    for desc, fmt, content_type in test_cases:
        print(f"\n[{desc}]")
        
        async with aiohttp.ClientSession() as session:
            try:
                headers = headers_base.copy()
                if content_type:
                    headers["Content-Type"] = content_type
                
                payload_data = {"username": "voo", "password": challenge}
                
                if fmt == "form" or fmt == "form_explicit":
                    # Form encoded
                    async with session.post(
                        url,
                        data=payload_data,
                        timeout=aiohttp.ClientTimeout(10),
                        headers=headers
                    ) as r:
                        response = await r.json()
                        result = "✓" if response.get("error") == "ok" else "✗"
                        print(f"  {result} {response.get('message', response.get('error'))}")
                
                elif "json" in fmt:
                    # JSON
                    async with session.post(
                        url,
                        json=payload_data,
                        timeout=aiohttp.ClientTimeout(10),
                        headers=headers
                    ) as r:
                        response = await r.json()
                        result = "✓" if response.get("error") == "ok" else "✗"
                        print(f"  {result} {response.get('message', response.get('error'))}")
            
            except Exception as e:
                print(f"  ✗ Error: {e}")
    
    # Also try different endpoints
    print("\n\n[Testing alternative endpoints]")
    alternative_endpoints = [
        "/api/v1/session/login",
        "/api/v1/login",
        "/api/login",
        "/api/session",
        "/login",
    ]
    
    for endpoint in alternative_endpoints:
        print(f"\n{endpoint}:")
        
        async with aiohttp.ClientSession() as session:
            try:
                full_url = f"{base_url}{endpoint}"
                data = {"username": "voo", "password": challenge}
                
                async with session.post(
                    full_url,
                    data=data,
                    timeout=aiohttp.ClientTimeout(5),
                    headers=headers_base
                ) as r:
                    try:
                        response = await r.json()
                        result = "✓" if response.get("error") == "ok" else "✗"
                        msg = response.get('message', response.get('error', 'unknown'))
                        print(f"  {result} {msg}")
                    except:
                        print(f"  - Status {r.status} (non-JSON response)")
            
            except asyncio.TimeoutError:
                print(f"  - Timeout (endpoint may not exist)")
            except Exception as e:
                print(f"  - Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_request_formats())
