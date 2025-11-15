# Test Organization

## Structure

Tests are organized by module with the following structure:

```
tests/
├── api/                    # API endpoint tests
├── core/                   # Core functionality tests
├── services/               # Service layer tests
├── models/                 # Database model tests
├── integration/            # Integration tests
├── unit/                   # Unit tests
└── README.md              # This file
```

## Naming Convention

All test files must follow the naming pattern:

```
yyMMdd_HHmm_<descriptive_name>.py
```

**Examples:**
- `251115_1430_test_auth_endpoints.py`
- `251115_1445_test_user_service.py`
- `251115_1500_test_api_key_model.py`

## Benefits

1. **Chronological Order**: Files are naturally sorted by creation date
2. **Easy Tracking**: Quickly identify when tests were added
3. **Version Control**: Clear history of test additions
4. **Module Organization**: Tests grouped by functional area

## Running Tests

```bash
# Run all tests
pytest

# Run tests for specific module
pytest tests/api/

# Run specific test file
pytest tests/api/251115_1430_test_auth_endpoints.py

# Run with coverage
pytest --cov=app --cov-report=html
```

## Writing New Tests

When creating a new test file:

1. Determine the appropriate module folder
2. Generate timestamp: `date +"%y%m%d_%H%M"`
3. Create file: `{timestamp}_test_{feature}.py`
4. Follow existing test patterns

## Example Test File

```python
# tests/api/251115_1430_test_auth_endpoints.py
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_register_user():
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "test@example.com",
            "username": "testuser",
            "password": "SecurePass123!",
            "full_name": "Test User"
        }
    )
    assert response.status_code == 201

def test_login_user():
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "test@example.com",
            "password": "SecurePass123!"
        }
    )
    assert response.status_code == 200
    assert "access_token" in response.json()
```
