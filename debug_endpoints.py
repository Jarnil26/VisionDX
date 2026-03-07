#!/usr/bin/env python
"""
Debug failing endpoints
"""
import asyncio
from httpx import AsyncClient


async def debug_endpoints():
    async with AsyncClient(base_url="http://127.0.0.1:8000") as client:
        print("Testing failing endpoints...\n")
        
        # Test 1: Doctor abnormal-reports
        print("1. GET /doctor/abnormal-reports")
        try:
            resp = await client.get("/doctor/abnormal-reports")
            print(f"   Status: {resp.status_code}")
            print(f"   Body: {resp.text[:500]}")
        except Exception as e:
            print(f"   Error: {e}")
        
        print("\n2. POST /upload-report")
        try:
            resp = await client.post("/upload-report", files={})
            print(f"   Status: {resp.status_code}")
            print(f"   Body: {resp.text[:500]}")
        except Exception as e:
            print(f"   Error: {e}")
        
        print("\n3. POST /users/login (no data)")
        try:
            resp = await client.post("/users/login", json={})
            print(f"   Status: {resp.status_code}")
            print(f"   Body: {resp.text[:500]}")
        except Exception as e:
            print(f"   Error: {e}")
        
        print("\n4. POST /users/login (with email/password)")
        try:
            resp = await client.post("/users/login", json={"email": "test@example.com", "password": "test"})
            print(f"   Status: {resp.status_code}")
            print(f"   Body: {resp.text[:500]}")
        except Exception as e:
            print(f"   Error: {e}")

asyncio.run(debug_endpoints())
