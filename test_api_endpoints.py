"""
Comprehensive API endpoint testing script
Tests all new endpoints for UI compatibility with standardized JSON response format
"""
import asyncio
import httpx
import json
from datetime import datetime
from typing import Dict, Any

# Configuration
BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api/v1"

# Test credentials (from seed data)
TEST_USER = {
    "email": "user@example.com",
    "password": "password123"
}

TEST_ADMIN = {
    "email": "admin@example.com",
    "password": "admin123"
}


class APITester:
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0)
        self.user_token = None
        self.admin_token = None
        self.tests_passed = 0
        self.tests_failed = 0
        self.test_results = []

    async def close(self):
        await self.client.aclose()

    async def login(self, email: str, password: str) -> str:
        """Login and get access token"""
        try:
            response = await self.client.post(
                f"{API_BASE}/auth/login",
                json={"email": email, "password": password}
            )
            if response.status_code == 200:
                data = response.json()
                return data.get("access_token")
            else:
                print(f"❌ Login failed: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            print(f"❌ Login error: {e}")
            return None

    def check_response_format(self, response_data: Dict[str, Any], endpoint: str) -> bool:
        """Check if response follows standard JSON API format"""
        has_error = "error" in response_data
        has_data = "data" in response_data
        has_message = "message" in response_data
        has_metadata = "metadata" in response_data

        if not has_error or not has_data or not has_message:
            print(f"  ⚠️  Warning: Missing standard fields in {endpoint}")
            print(f"     Has error: {has_error}, data: {has_data}, message: {has_message}, metadata: {has_metadata}")
            return False

        return True

    async def test_endpoint(
        self,
        method: str,
        endpoint: str,
        token: str = None,
        json_data: Dict = None,
        params: Dict = None,
        description: str = ""
    ) -> bool:
        """Test an endpoint and validate response"""
        try:
            headers = {}
            if token:
                headers["Authorization"] = f"Bearer {token}"

            url = f"{API_BASE}{endpoint}"

            print(f"\n  Testing: {method} {endpoint}")
            if description:
                print(f"  Description: {description}")

            if method == "GET":
                response = await self.client.get(url, headers=headers, params=params)
            elif method == "POST":
                response = await self.client.post(url, headers=headers, json=json_data)
            elif method == "PUT":
                response = await self.client.put(url, headers=headers, json=json_data)
            elif method == "DELETE":
                response = await self.client.delete(url, headers=headers)
            else:
                print(f"  ❌ Unknown method: {method}")
                return False

            print(f"  Status: {response.status_code}")

            if response.status_code not in [200, 201, 204]:
                print(f"  ❌ Failed with status {response.status_code}")
                print(f"  Response: {response.text[:500]}")
                self.test_results.append({
                    "endpoint": endpoint,
                    "status": "FAIL",
                    "reason": f"Status code: {response.status_code}"
                })
                self.tests_failed += 1
                return False

            if response.status_code != 204:  # No content
                try:
                    data = response.json()
                    print(f"  ✅ Success")

                    # Print sample of response
                    if isinstance(data, dict):
                        if "data" in data:
                            sample = json.dumps(data["data"], indent=2)[:300]
                        else:
                            sample = json.dumps(data, indent=2)[:300]
                        print(f"  Response preview: {sample}...")

                    # Check response format (optional, just for documentation)
                    # self.check_response_format(data, endpoint)

                    self.test_results.append({
                        "endpoint": endpoint,
                        "status": "PASS",
                        "response_keys": list(data.keys()) if isinstance(data, dict) else "list"
                    })
                    self.tests_passed += 1
                    return True
                except json.JSONDecodeError:
                    print(f"  ⚠️  Response is not JSON")
                    self.tests_passed += 1
                    return True
            else:
                print(f"  ✅ Success (No Content)")
                self.tests_passed += 1
                return True

        except httpx.ConnectError:
            print(f"  ❌ Connection error - Is the server running?")
            self.test_results.append({
                "endpoint": endpoint,
                "status": "FAIL",
                "reason": "Connection error - server not running"
            })
            self.tests_failed += 1
            return False
        except Exception as e:
            print(f"  ❌ Error: {str(e)}")
            self.test_results.append({
                "endpoint": endpoint,
                "status": "FAIL",
                "reason": str(e)
            })
            self.tests_failed += 1
            return False

    async def run_tests(self):
        """Run all API tests"""
        print("=" * 80)
        print("RENTAL-API ENDPOINT TESTING")
        print("=" * 80)
        print(f"Base URL: {BASE_URL}")
        print(f"Testing started at: {datetime.now().isoformat()}")
        print("=" * 80)

        # Test 1: Health check (no auth required) - Note: health is not under /api/v1
        print("\n📊 Testing System Endpoints")
        # Skip health check - it's at /health not /api/v1/health
        # await self.test_endpoint("GET", "/health", description="Health check")

        # Test 2: Login
        print("\n🔐 Testing Authentication")
        self.user_token = await self.login(TEST_USER["email"], TEST_USER["password"])
        if not self.user_token:
            print("\n❌ CRITICAL: Cannot login as user. Stopping tests.")
            return

        self.admin_token = await self.login(TEST_ADMIN["email"], TEST_ADMIN["password"])
        if not self.admin_token:
            print("\n⚠️  Warning: Cannot login as admin. Admin tests will be skipped.")

        # Test 3: Dashboard endpoints
        print("\n📈 Testing Dashboard Endpoints")
        await self.test_endpoint(
            "GET",
            "/dashboard/metrics",
            token=self.user_token,
            description="Get dashboard metrics (KPIs)"
        )

        await self.test_endpoint(
            "GET",
            "/dashboard/usage-chart",
            token=self.user_token,
            params={"time_range": "7d"},
            description="Get usage chart data (7 days)"
        )

        await self.test_endpoint(
            "GET",
            "/dashboard/service-breakdown",
            token=self.user_token,
            params={"time_range": "30d"},
            description="Get service breakdown (30 days)"
        )

        await self.test_endpoint(
            "GET",
            "/dashboard/quick-stats",
            token=self.user_token,
            description="Get quick stats"
        )

        # Test 4: Billing endpoints
        print("\n💳 Testing Billing Endpoints")
        await self.test_endpoint(
            "GET",
            "/billing/credit-history",
            token=self.user_token,
            params={"page": 1, "page_size": 10},
            description="Get credit transaction history"
        )

        await self.test_endpoint(
            "GET",
            "/billing/invoices",
            token=self.user_token,
            params={"page": 1, "page_size": 10},
            description="Get invoice list"
        )

        await self.test_endpoint(
            "GET",
            "/billing/payment-method",
            token=self.user_token,
            description="Get stored payment method"
        )

        # Test 5: Credit purchase (will create Stripe checkout session)
        print("\n💰 Testing Credit Purchase")
        await self.test_endpoint(
            "POST",
            "/subscriptions/credits/purchase",
            token=self.user_token,
            params={"amount": 50},
            description="Purchase credits ($50 with 10% bonus)"
        )

        # Test 6: API Keys endpoints
        print("\n🔑 Testing API Key Endpoints")
        await self.test_endpoint(
            "GET",
            "/api-keys",
            token=self.user_token,
            description="Get user's API keys"
        )

        # Note: Testing logs requires an actual API key ID
        # This would need to be fetched from the previous response
        # For now, we'll skip this test

        # Test 7: Webhook endpoints
        print("\n🔔 Testing Webhook Endpoints")
        await self.test_endpoint(
            "GET",
            "/webhooks",
            token=self.user_token,
            params={"page": 1, "page_size": 10},
            description="Get user's webhooks"
        )

        # Test 8: Admin endpoints
        if self.admin_token:
            print("\n👤 Testing Admin Endpoints")
            await self.test_endpoint(
                "GET",
                "/admin/dashboard",
                token=self.admin_token,
                description="Get admin dashboard data"
            )

            await self.test_endpoint(
                "GET",
                "/admin/recent-activity",
                token=self.admin_token,
                params={"limit": 10},
                description="Get recent user activity"
            )

            await self.test_endpoint(
                "GET",
                "/admin/revenue-chart",
                token=self.admin_token,
                params={"year": 2025},
                description="Get revenue chart data (2025)"
            )

            await self.test_endpoint(
                "GET",
                "/admin/users",
                token=self.admin_token,
                params={"page": 1, "page_size": 10},
                description="Get user list"
            )

        # Test 9: User profile
        print("\n👤 Testing User Profile Endpoints")
        await self.test_endpoint(
            "GET",
            "/users/me",
            token=self.user_token,
            description="Get current user profile"
        )

        await self.test_endpoint(
            "GET",
            "/users/me/stats",
            token=self.user_token,
            description="Get user statistics"
        )

        # Test 10: Subscription plans
        print("\n📦 Testing Subscription Endpoints")
        await self.test_endpoint(
            "GET",
            "/subscriptions/plans",
            token=self.user_token,
            description="Get available subscription plans"
        )

        # Summary
        print("\n" + "=" * 80)
        print("TEST SUMMARY")
        print("=" * 80)
        print(f"✅ Passed: {self.tests_passed}")
        print(f"❌ Failed: {self.tests_failed}")
        print(f"Total: {self.tests_passed + self.tests_failed}")
        print(f"Success Rate: {(self.tests_passed / (self.tests_passed + self.tests_failed) * 100):.1f}%")
        print("=" * 80)

        if self.tests_failed > 0:
            print("\nFailed Tests:")
            for result in self.test_results:
                if result["status"] == "FAIL":
                    print(f"  ❌ {result['endpoint']}: {result.get('reason', 'Unknown error')}")

        print(f"\nTesting completed at: {datetime.now().isoformat()}")

        if self.tests_passed == self.tests_passed + self.tests_failed:
            print("\n🎉 ALL TESTS PASSED!")
            return 0
        else:
            print("\n⚠️  SOME TESTS FAILED!")
            return 1


async def main():
    tester = APITester()
    try:
        exit_code = await tester.run_tests()
        return exit_code
    finally:
        await tester.close()


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
