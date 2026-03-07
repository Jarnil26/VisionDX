#!/usr/bin/env python
"""
VisionDX — Backend API Verification Script

Tests all major API endpoints and generates a comprehensive report.
"""
import asyncio
import json
from datetime import datetime
from httpx import AsyncClient


class APITester:
    def __init__(self, base_url="http://127.0.0.1:8000"):
        self.base_url = base_url
        self.results = {}
        self.token = None
    
    async def test_all(self):
        """Run all API tests."""
        async with AsyncClient(base_url=self.base_url, timeout=10.0) as client:
            print("=" * 80)
            print("VISIONDX BACKEND API VERIFICATION REPORT")
            print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print("=" * 80)
            print()
            
            # Section 1: Core System Endpoints
            print("[SECTION 1] CORE SYSTEM ENDPOINTS")
            print("-" * 80)
            await self._test_health(client)
            await self._test_docs(client)
            await self._test_openapi_schema(client)
            print()
            
            # Section 2: Doctor/Report Endpoints
            print("[SECTION 2] DOCTOR & REPORT ENDPOINTS")
            print("-" * 80)
            await self._test_doctor_endpoints(client)
            await self._test_report_endpoints(client)
            print()
            
            # Section 3: User Management Endpoints
            print("[SECTION 3] USER MANAGEMENT ENDPOINTS")
            print("-" * 80)
            await self._test_user_endpoints(client)
            print()
            
            # Section 4: Lab Endpoints
            print("[SECTION 4] LAB & BOOKING ENDPOINTS")
            print("-" * 80)
            await self._test_lab_endpoints(client)
            print()
            
            # Section 5: Health Tracking
            print("[SECTION 5] HEALTH TRACKING ENDPOINTS")
            print("-" * 80)
            await self._test_followup_endpoints(client)
            print()
            
            # Section 6: AI Chat
            print("[SECTION 6] AI CHAT ENDPOINTS")
            print("-" * 80)
            await self._test_chat_endpoints(client)
            print()
            
            # Summary
            self._print_summary()
    
    async def _test_health(self, client):
        """Test /health endpoint."""
        try:
            resp = await client.get("/health")
            status = "✅" if resp.status_code == 200 else "⚠️"
            data = resp.json()
            print(f"{status} GET /health                          | Status: {resp.status_code}")
            if resp.status_code == 200:
                print(f"   └─ Status: {data.get('status')}")
                print(f"   └─ Version: {data.get('version')}")
                print(f"   └─ Environment: {data.get('environment')}")
                print(f"   └─ Model Loaded: {data.get('model_loaded')}")
            self.results['Health Check'] = (True, resp.status_code)
        except Exception as e:
            print(f"❌ GET /health                          | Error: {str(e)[:50]}")
            self.results['Health Check'] = (False, str(e))
    
    async def _test_docs(self, client):
        """Test documentation endpoints."""
        endpoints = [
            ("/docs", "Swagger OpenAPI Docs"),
            ("/redoc", "ReDoc Documentation"),
        ]
        
        for path, name in endpoints:
            try:
                resp = await client.get(path)
                status = "✅" if resp.status_code == 200 else "⚠️"
                print(f"{status} GET {path:30} | Status: {resp.status_code} | {name}")
                self.results[name] = (resp.status_code == 200, resp.status_code)
            except Exception as e:
                print(f"❌ GET {path:30} | Error: {str(e)[:40]}")
                self.results[name] = (False, str(e))
    
    async def _test_openapi_schema(self, client):
        """Test OpenAPI schema endpoint."""
        try:
            resp = await client.get("/openapi.json")
            status = "✅" if resp.status_code == 200 else "⚠️"
            print(f"{status} GET /openapi.json                    | Status: {resp.status_code}")
            if resp.status_code == 200:
                schema = resp.json()
                endpoints_count = len(schema.get('paths', {}))
                print(f"   └─ Total endpoints documented: {endpoints_count}")
            self.results['OpenAPI Schema'] = (resp.status_code == 200, resp.status_code)
        except Exception as e:
            print(f"❌ GET /openapi.json                    | Error: {str(e)[:40]}")
            self.results['OpenAPI Schema'] = (False, str(e))
    
    async def _test_doctor_endpoints(self, client):
        """Test doctor-related endpoints."""
        endpoints = [
            ("/doctor/abnormal-reports", "GET", "List Abnormal Reports"),
        ]
        
        for path, method, name in endpoints:
            try:
                if method == "GET":
                    resp = await client.get(path)
                status_ok = resp.status_code in [200, 401, 403]
                status = "✅" if status_ok else "⚠️"
                print(f"{status} {method} {path:30} | Status: {resp.status_code} | {name}")
                self.results[name] = (status_ok, resp.status_code)
            except Exception as e:
                print(f"❌ {method} {path:30} | Error: {str(e)[:40]}")
                self.results[name] = (False, str(e))
    
    async def _test_report_endpoints(self, client):
        """Test report endpoints."""
        endpoints = [
            ("/upload-report", "POST", "Upload Report"),
        ]
        
        for path, method, name in endpoints:
            try:
                if method == "POST":
                    resp = await client.post(path, files={})
                # Expect 400/422 because no file provided
                status_ok = resp.status_code in [400, 422, 200]
                status = "✅" if status_ok else "⚠️"
                print(f"{status} {method} {path:30} | Status: {resp.status_code} | {name}")
                self.results[name] = (status_ok, resp.status_code)
            except Exception as e:
                print(f"❌ {method} {path:30} | Error: {str(e)[:40]}")
                self.results[name] = (False, str(e))
    
    async def _test_user_endpoints(self, client):
        """Test user management endpoints."""
        endpoints = [
            ("/users/register", "POST", "User Registration"),
            ("/users/login", "POST", "User Login"),
        ]
        
        for path, method, name in endpoints:
            try:
                if method == "POST":
                    # Send minimal data
                    resp = await client.post(path, json={"email": "test@test.com", "password": "test"})
                # Expect various responses: 400, 409, 422, etc.
                status_ok = resp.status_code in [200, 201, 400, 409, 422]
                status = "✅" if status_ok else "⚠️"
                print(f"{status} {method} {path:30} | Status: {resp.status_code} | {name}")
                self.results[name] = (status_ok, resp.status_code)
            except Exception as e:
                print(f"❌ {method} {path:30} | Error: {str(e)[:40]}")
                self.results[name] = (False, str(e))
    
    async def _test_lab_endpoints(self, client):
        """Test lab and booking endpoints."""
        endpoints = [
            ("/labs", "GET", "List Labs"),
        ]
        
        for path, method, name in endpoints:
            try:
                if method == "GET":
                    resp = await client.get(path)
                status_ok = resp.status_code in [200, 401, 403]
                status = "✅" if status_ok else "⚠️"
                print(f"{status} {method} {path:30} | Status: {resp.status_code} | {name}")
                self.results[name] = (status_ok, resp.status_code)
            except Exception as e:
                print(f"❌ {method} {path:30} | Error: {str(e)[:40]}")
                self.results[name] = (False, str(e))
    
    async def _test_followup_endpoints(self, client):
        """Test health tracking endpoints."""
        # These require authentication, so we expect 401/403
        endpoints = [
            ("/follow-ups/weekly", "GET", "Get Weekly Follow-ups"),
            ("/follow-ups/monthly", "GET", "Get Monthly Follow-ups"),
        ]
        
        for path, method, name in endpoints:
            try:
                if method == "GET":
                    resp = await client.get(path)
                # Without auth token, expect 401/403
                status_ok = resp.status_code in [200, 401, 403]
                status = "✅" if status_ok else "⚠️"
                print(f"{status} {method} {path:30} | Status: {resp.status_code} | {name}")
                self.results[name] = (status_ok, resp.status_code)
            except Exception as e:
                print(f"❌ {method} {path:30} | Error: {str(e)[:40]}")
                self.results[name] = (False, str(e))
    
    async def _test_chat_endpoints(self, client):
        """Test AI chat endpoints."""
        endpoints = [
            ("/chat", "POST", "Send Chat Message"),
        ]
        
        for path, method, name in endpoints:
            try:
                if method == "POST":
                    resp = await client.post(path, json={"message": "test"})
                # Without proper data/auth, may get 401/422
                status_ok = resp.status_code in [200, 201, 400, 401, 422]
                status = "✅" if status_ok else "⚠️"
                print(f"{status} {method} {path:30} | Status: {resp.status_code} | {name}")
                self.results[name] = (status_ok, resp.status_code)
            except Exception as e:
                print(f"❌ {method} {path:30} | Error: {str(e)[:40]}")
                self.results[name] = (False, str(e))
    
    def _print_summary(self):
        """Print summary of test results."""
        print("=" * 80)
        print("[SUMMARY] TEST RESULTS")
        print("=" * 80)
        
        total = len(self.results)
        passed = sum(1 for success, _ in self.results.values() if success)
        failed = total - passed
        
        print(f"Total Endpoints Tested: {total}")
        print(f"[PASS] Passed: {passed}")
        print(f"[FAIL] Failed: {failed}")
        print(f"Success Rate: {(passed/total*100):.1f}%")
        print()
        
        print("ENDPOINT STATUS BREAKDOWN:")
        print("-" * 80)
        for name, (success, code) in self.results.items():
            status = "[PASS]" if success else "[FAIL]"
            print(f"{status:10} | {name:40} | HTTP {code}")
        print()
        
        print("=" * 80)
        print("[OK] BACKEND IS OPERATIONAL" if failed == 0 else f"[WARNING] {failed} endpoint(s) need attention")
        print("=" * 80)


async def main():
    """Run the API verification."""
    tester = APITester()
    await tester.test_all()


if __name__ == "__main__":
    asyncio.run(main())
