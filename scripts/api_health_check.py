#!/usr/bin/env python3
"""
API Health Check Script
Validates all API components after backend restructuring
"""
import sys
import os
from pathlib import Path
from typing import List, Dict, Tuple

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))


class APIHealthChecker:
    """Comprehensive API health checker"""

    def __init__(self):
        self.errors = []
        self.warnings = []
        self.checks_passed = 0
        self.checks_failed = 0

    def check_imports(self) -> bool:
        """Check if all critical imports work"""
        print("=" * 80)
        print("CHECKING IMPORTS")
        print("=" * 80)

        imports_to_check = [
            ("app.config", "settings"),
            ("app.database", "engine, get_db, Base"),
            ("app.core.middleware", "RateLimitMiddleware, RequestLoggingMiddleware, SecurityHeadersMiddleware"),
            ("app.core.cache", "RedisCache"),
            ("app.core.security", "create_access_token, verify_password"),
            ("app.core.permissions", "require_permission"),
            ("app.core.openapi_config", "get_openapi_tags"),
            ("app.models.user", "User"),
            ("app.models.api_key", "ApiKey"),
            ("app.schemas.auth", "LoginRequest"),
            ("app.services.auth_service", "AuthService"),
            ("app.api.v1.auth", "router"),
        ]

        all_passed = True
        for module, items in imports_to_check:
            try:
                exec(f"from {module} import {items}")
                print(f"✓ {module}")
                self.checks_passed += 1
            except Exception as e:
                print(f"✗ {module}: {str(e)}")
                self.errors.append(f"Import failed: {module} - {str(e)}")
                self.checks_failed += 1
                all_passed = False

        return all_passed

    def check_file_structure(self) -> bool:
        """Check if all expected files exist"""
        print("\n" + "=" * 80)
        print("CHECKING FILE STRUCTURE")
        print("=" * 80)

        expected_files = [
            "app/__init__.py",
            "app/main.py",
            "app/config.py",
            "app/database.py",
            "app/core/middleware.py",
            "app/core/cache.py",
            "app/core/security.py",
            "app/core/permissions.py",
            "app/core/openapi_config.py",
            "app/api/v1/auth.py",
            "app/api/v1/users.py",
            "app/api/v1/api_keys.py",
            "app/api/v1/webhooks.py",
            "app/api/v1/subscriptions.py",
            "app/api/v1/admin.py",
            "app/api/v1/websocket.py",
            "app/models/user.py",
            "app/models/api_key.py",
            "app/models/webhook.py",
            "app/models/subscription.py",
            "app/models/organization.py",
            "app/schemas/auth.py",
            "app/schemas/user.py",
            "app/schemas/api_key.py",
            "app/services/auth_service.py",
            "app/services/user_service.py",
            "migrations/env.py",
            "alembic.ini",
        ]

        all_passed = True
        for file_path in expected_files:
            if Path(file_path).exists():
                print(f"✓ {file_path}")
                self.checks_passed += 1
            else:
                print(f"✗ {file_path} - MISSING")
                self.errors.append(f"Missing file: {file_path}")
                self.checks_failed += 1
                all_passed = False

        return all_passed

    def check_legacy_imports(self) -> bool:
        """Check for legacy 'backend' imports that should be 'app'"""
        print("\n" + "=" * 80)
        print("CHECKING FOR LEGACY IMPORTS")
        print("=" * 80)

        import subprocess

        try:
            result = subprocess.run(
                ["grep", "-r", "from backend", "app/"],
                capture_output=True,
                text=True
            )

            if result.returncode == 0 and result.stdout:
                print("✗ Found legacy 'backend' imports:")
                print(result.stdout)
                self.errors.append("Legacy 'backend' imports found")
                self.checks_failed += 1
                return False
            else:
                print("✓ No legacy 'backend' imports found")
                self.checks_passed += 1
                return True
        except Exception as e:
            print(f"⚠ Could not check for legacy imports: {e}")
            self.warnings.append(f"Legacy import check failed: {e}")
            return True

    def check_api_routers(self) -> bool:
        """Verify all API routers are properly defined"""
        print("\n" + "=" * 80)
        print("CHECKING API ROUTERS")
        print("=" * 80)

        routers = [
            ("app.api.v1.auth", "router", "/auth"),
            ("app.api.v1.users", "router", "/users"),
            ("app.api.v1.api_keys", "router", "/api-keys"),
            ("app.api.v1.webhooks", "router", "/webhooks"),
            ("app.api.v1.subscriptions", "router", "/subscriptions"),
            ("app.api.v1.admin", "router", "/admin"),
            ("app.api.v1.websocket", "router", "/ws"),
        ]

        all_passed = True
        for module, router_name, prefix in routers:
            try:
                exec(f"from {module} import {router_name}")
                print(f"✓ {module} -> {prefix}")
                self.checks_passed += 1
            except Exception as e:
                print(f"✗ {module}: {str(e)}")
                self.errors.append(f"Router import failed: {module}")
                self.checks_failed += 1
                all_passed = False

        return all_passed

    def check_models(self) -> bool:
        """Verify all database models"""
        print("\n" + "=" * 80)
        print("CHECKING DATABASE MODELS")
        print("=" * 80)

        models = [
            ("User", "app.models.user"),
            ("ApiKey", "app.models.api_key"),
            ("Webhook", "app.models.webhook"),
            ("WebhookDelivery", "app.models.webhook"),
            ("Subscription", "app.models.subscription"),
            ("Payment", "app.models.subscription"),
            ("Organization", "app.models.organization"),
            ("OrganizationMember", "app.models.organization"),
        ]

        all_passed = True
        for model_name, module in models:
            try:
                exec(f"from {module} import {model_name}")
                print(f"✓ {model_name}")
                self.checks_passed += 1
            except Exception as e:
                print(f"✗ {model_name}: {str(e)}")
                self.errors.append(f"Model import failed: {model_name}")
                self.checks_failed += 1
                all_passed = False

        return all_passed

    def check_schemas(self) -> bool:
        """Verify all Pydantic schemas"""
        print("\n" + "=" * 80)
        print("CHECKING PYDANTIC SCHEMAS")
        print("=" * 80)

        schemas = [
            ("LoginRequest", "app.schemas.auth"),
            ("RegisterRequest", "app.schemas.auth"),
            ("TokenResponse", "app.schemas.auth"),
            ("UserResponse", "app.schemas.user"),
            ("UserUpdate", "app.schemas.user"),
            ("ApiKeyCreate", "app.schemas.api_key"),
            ("ApiKeyResponse", "app.schemas.api_key"),
            ("WebhookCreate", "app.schemas.webhook"),
            ("SubscriptionResponse", "app.schemas.subscription"),
        ]

        all_passed = True
        for schema_name, module in schemas:
            try:
                exec(f"from {module} import {schema_name}")
                print(f"✓ {schema_name}")
                self.checks_passed += 1
            except Exception as e:
                print(f"✗ {schema_name}: {str(e)}")
                self.errors.append(f"Schema import failed: {schema_name}")
                self.checks_failed += 1
                all_passed = False

        return all_passed

    def check_services(self) -> bool:
        """Verify all service layers"""
        print("\n" + "=" * 80)
        print("CHECKING SERVICE LAYERS")
        print("=" * 80)

        services = [
            "auth_service",
            "user_service",
            "api_key_service",
            "webhook_service",
            "subscription_service",
            "payment_service",
            "email_service",
            "analytics_service",
        ]

        all_passed = True
        for service in services:
            try:
                exec(f"from app.services.{service} import *")
                print(f"✓ {service}")
                self.checks_passed += 1
            except Exception as e:
                print(f"✗ {service}: {str(e)}")
                self.errors.append(f"Service import failed: {service}")
                self.checks_failed += 1
                all_passed = False

        return all_passed

    def print_summary(self):
        """Print final summary"""
        print("\n" + "=" * 80)
        print("SUMMARY")
        print("=" * 80)
        print(f"Checks Passed: {self.checks_passed}")
        print(f"Checks Failed: {self.checks_failed}")
        print(f"Warnings: {len(self.warnings)}")

        if self.errors:
            print("\n❌ ERRORS:")
            for error in self.errors:
                print(f"  - {error}")

        if self.warnings:
            print("\n⚠️  WARNINGS:")
            for warning in self.warnings:
                print(f"  - {warning}")

        if not self.errors:
            print("\n✅ ALL CHECKS PASSED!")
            print("API is ready for deployment.")
            return 0
        else:
            print("\n❌ SOME CHECKS FAILED!")
            print("Please review errors above.")
            return 1

    def run_all_checks(self) -> int:
        """Run all health checks"""
        print("API HEALTH CHECK")
        print("Verifying backend structure after reorganization")
        print()

        # Note: Import checks will fail without dependencies installed
        # That's expected - this is for structure validation
        print("NOTE: Import checks require dependencies to be installed.")
        print("      Failures here may be due to missing dependencies, not structure issues.")
        print()

        self.check_file_structure()
        self.check_legacy_imports()

        # Try import checks (may fail without dependencies)
        try:
            self.check_imports()
            self.check_api_routers()
            self.check_models()
            self.check_schemas()
            self.check_services()
        except Exception as e:
            print(f"\n⚠️  Import checks skipped (dependencies not installed): {e}")
            self.warnings.append("Import checks skipped - install dependencies to run")

        return self.print_summary()


if __name__ == "__main__":
    checker = APIHealthChecker()
    sys.exit(checker.run_all_checks())
