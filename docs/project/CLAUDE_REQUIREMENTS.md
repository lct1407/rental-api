# Claude AI Development Requirements

**Version**: 2.0
**Last Updated**: 2025-11-15

This document outlines mandatory requirements for AI assistants working on the RentAPI codebase.

---

## 1. Documentation Organization

### 1.1 Documentation Structure

All documentation files MUST be organized in the `docs/` folder with consistent subfolders:

```
docs/
├── api/                    # API documentation
│   ├── API_DOCUMENTATION.md
│   └── BACKEND_API.md
├── deployment/             # Deployment guides
│   └── DEPLOYMENT.md
├── guides/                 # User and developer guides
│   └── STARTUP_GUIDE.md
├── architecture/           # Architecture decisions and diagrams
├── project/                # Project management docs
│   ├── IMPLEMENTATION_STATUS.md
│   ├── PR_DESCRIPTION.md
│   └── CLAUDE_REQUIREMENTS.md
└── README.md              # Docs index
```

### 1.2 Documentation Rules

**MUST:**
- ✅ Place all new documentation in appropriate `docs/` subfolder
- ✅ Use clear, descriptive filenames
- ✅ Include table of contents for documents >100 lines
- ✅ Keep API docs in `docs/api/`
- ✅ Keep deployment docs in `docs/deployment/`
- ✅ Keep guides in `docs/guides/`
- ✅ Update docs/README.md when adding new categories

**MUST NOT:**
- ❌ Create documentation files in root directory
- ❌ Use abbreviations in folder names
- ❌ Mix different doc types in same folder
- ❌ Create nested folders beyond 2 levels

---

## 2. Test File Organization

### 2.1 Test Structure

All test files MUST be organized by module in the `tests/` folder:

```
tests/
├── api/                    # API endpoint tests
│   ├── 251115_1430_test_auth_endpoints.py
│   └── 251115_1445_test_user_endpoints.py
├── core/                   # Core functionality tests
│   ├── 251115_1500_test_security.py
│   └── 251115_1515_test_cache.py
├── services/               # Service layer tests
│   ├── 251115_1530_test_auth_service.py
│   └── 251115_1545_test_user_service.py
├── models/                 # Database model tests
│   └── 251115_1600_test_user_model.py
├── integration/            # Integration tests
│   └── 251115_1615_test_payment_flow.py
├── unit/                   # Unit tests
│   └── 251115_1630_test_validators.py
└── README.md              # Test documentation
```

### 2.2 Test File Naming Convention

**FORMAT**: `yyMMdd_HHmm_<descriptive_name>.py`

**Components:**
- `yy` - Two-digit year (e.g., `25` for 2025)
- `MM` - Two-digit month (e.g., `11` for November)
- `dd` - Two-digit day (e.g., `15`)
- `HH` - Two-digit hour in 24h format (e.g., `14` for 2:00 PM)
- `mm` - Two-digit minute (e.g., `30`)
- `<descriptive_name>` - Clear description with underscores

**Examples:**
```
✅ 251115_1430_test_auth_endpoints.py
✅ 251115_1445_test_user_service.py
✅ 251115_1500_test_payment_integration.py
✅ 251115_1515_test_webhook_delivery.py

❌ test_auth.py                    # Missing timestamp
❌ 2025_11_15_test_auth.py         # Wrong date format
❌ 251115_test_auth.py             # Missing time
❌ 251115_1430-test-auth.py        # Using dashes instead of underscores
```

### 2.3 Test Organization Rules

**MUST:**
- ✅ Use timestamp prefix for ALL test files: `date +"%y%m%d_%H%M"`
- ✅ Place tests in appropriate module folder
- ✅ Use descriptive names after timestamp
- ✅ Include `test_` prefix after timestamp
- ✅ Group related tests in same folder
- ✅ Update tests/README.md with examples

**MUST NOT:**
- ❌ Create test files without timestamp prefix
- ❌ Use dates in other formats
- ❌ Place tests directly in `tests/` root
- ❌ Mix different test types in same folder

### 2.4 Benefits of Timestamp Naming

1. **Chronological Order**: Files naturally sort by creation date
2. **Easy Tracking**: Quickly identify when tests were added
3. **Version Control**: Clear history of test evolution
4. **Merge Conflicts**: Reduced conflicts (unique timestamps)
5. **Test Coverage**: See testing activity over time

### 2.5 Creating New Test Files

**Step-by-step:**

1. Determine module folder (api, core, services, models, integration, unit)
2. Generate timestamp: `date +"%y%m%d_%H%M"`
3. Create file: `{module}/{timestamp}_test_{feature}.py`
4. Write tests following existing patterns

**Example:**
```bash
# Generate timestamp
TIMESTAMP=$(date +"%y%m%d_%H%M")

# Create test file
touch tests/api/${TIMESTAMP}_test_subscription_endpoints.py

# Result: tests/api/251115_1430_test_subscription_endpoints.py
```

---

## 3. Requirements Organization

### 3.1 Requirements Structure

Dependencies are organized into TWO files:

```
requirements/
├── base.txt              # Core dependencies (REQUIRED)
├── advanced.txt          # Advanced features (OPTIONAL)
├── requirements.txt      # Legacy (deprecated)
├── requirements-dev.txt  # Development tools
└── README.md            # Installation guide
```

### 3.2 Base Requirements (base.txt)

**Contains:**
- FastAPI framework
- Database (SQLAlchemy, Alembic, AsyncPG)
- Authentication (JWT, bcrypt, cryptography)
- Validation (Pydantic)
- Configuration (python-dotenv, python-decouple)
- HTTP client (httpx)
- Date/time utilities

**Installation:**
```bash
pip install -r requirements/base.txt
```

### 3.3 Advanced Requirements (advanced.txt)

**Organized by feature with comment sections:**

1. **REDIS** - Caching and rate limiting
2. **AUTHENTICATION** - 2FA and phone validation
3. **BACKGROUND TASKS** - Celery workers
4. **EMAIL** - Email sending and templates
5. **PAYMENTS** - Stripe and PayPal integration
6. **STORAGE** - AWS S3 cloud storage
7. **WEBSOCKET** - Real-time communication
8. **MONITORING** - Prometheus, logging, tracing
9. **REPORTING** - PDF generation, data processing
10. **UTILITIES** - Additional production tools

**Installation:**
```bash
# Full advanced features
pip install -r requirements/advanced.txt

# Or selectively install (copy specific sections)
```

### 3.4 Requirements Rules

**MUST:**
- ✅ Add new dependencies to appropriate file (base or advanced)
- ✅ Pin specific versions (e.g., `fastapi==0.109.0`)
- ✅ Add comment section headers in advanced.txt
- ✅ Group related dependencies together
- ✅ Test in isolated environment before committing
- ✅ Update requirements/README.md if adding new category

**MUST NOT:**
- ❌ Add dependencies without version pins
- ❌ Modify requirements.txt (it's deprecated)
- ❌ Mix base and advanced dependencies
- ❌ Add development tools to base or advanced (use requirements-dev.txt)

### 3.5 Adding New Dependencies

**Process:**

1. **Determine category**: Is it base (core) or advanced (optional)?
2. **Find appropriate section**: Which feature category in advanced.txt?
3. **Pin version**: Always specify exact version
4. **Test installation**: Verify in clean environment
5. **Update docs**: Add to requirements/README.md if new category

**Example - Adding a new monitoring tool:**

```txt
# In requirements/advanced.txt, find MONITORING section:

# ============================================================================
# MONITORING - Prometheus, Logging, and Tracing
# ============================================================================
prometheus-fastapi-instrumentator==6.1.0
prometheus-client==0.19.0
python-json-logger==2.0.7
structlog==24.1.0
opentelemetry-api==1.22.0
opentelemetry-sdk==1.22.0
opentelemetry-instrumentation-fastapi==0.43b0
sentry-sdk[fastapi]==1.40.0  # <- Add here with comment
```

---

## 4. File Organization Summary

### 4.1 Root Directory Structure

```
rental-api/
├── app/                    # Backend application code
├── client/                 # Frontend React application
├── docs/                   # ALL documentation (organized)
│   ├── api/
│   ├── deployment/
│   ├── guides/
│   ├── architecture/
│   └── project/
├── migrations/             # Database migrations
├── requirements/           # Python dependencies (organized)
│   ├── base.txt
│   ├── advanced.txt
│   └── README.md
├── scripts/                # Utility scripts
├── tests/                  # All tests (organized by module)
│   ├── api/
│   ├── core/
│   ├── services/
│   ├── models/
│   ├── integration/
│   └── unit/
├── alembic.ini            # Alembic configuration
├── .env.example           # Environment template
├── CLAUDE.md              # AI assistant guide (main)
└── README.md              # Project README
```

### 4.2 What Goes Where

| File Type | Location | Example |
|-----------|----------|---------|
| API documentation | `docs/api/` | `API_DOCUMENTATION.md` |
| Deployment guide | `docs/deployment/` | `DEPLOYMENT.md` |
| User guides | `docs/guides/` | `STARTUP_GUIDE.md` |
| Architecture docs | `docs/architecture/` | `SYSTEM_DESIGN.md` |
| Project management | `docs/project/` | `IMPLEMENTATION_STATUS.md` |
| API tests | `tests/api/` | `251115_1430_test_auth.py` |
| Service tests | `tests/services/` | `251115_1445_test_user_service.py` |
| Core dependencies | `requirements/base.txt` | `fastapi==0.109.0` |
| Optional features | `requirements/advanced.txt` | `celery==5.3.4` |

---

## 5. Compliance Checklist

Before committing changes, verify:

### Documentation
- [ ] All docs in appropriate `docs/` subfolder
- [ ] No documentation files in root (except README.md, CLAUDE.md)
- [ ] Docs follow naming conventions
- [ ] Table of contents added for long documents

### Tests
- [ ] Test files have timestamp prefix (yyMMdd_HHmm_)
- [ ] Tests in correct module folder
- [ ] Test filenames are descriptive
- [ ] tests/README.md updated if new patterns added

### Requirements
- [ ] Dependencies in correct file (base vs advanced)
- [ ] Versions pinned (no `>=` or `~=`)
- [ ] Grouped in appropriate section with comments
- [ ] Tested in isolated environment
- [ ] requirements/README.md updated if needed

### General
- [ ] No files in wrong locations
- [ ] Consistent naming conventions followed
- [ ] Related files grouped logically
- [ ] Documentation updated to reflect changes

---

## 6. Automated Checks

Consider adding pre-commit hooks to enforce these requirements:

```bash
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: check-test-naming
        name: Check test file naming
        entry: python scripts/check_test_naming.py
        language: system
        files: ^tests/.*\.py$

      - id: check-docs-location
        name: Check docs are in docs/
        entry: python scripts/check_docs_location.py
        language: system
        files: \.md$
```

---

## 7. Examples

### Good Examples ✅

```
docs/api/PAYMENT_API.md
docs/deployment/DOCKER_SETUP.md
tests/api/251115_1430_test_auth_endpoints.py
tests/services/251115_1445_test_payment_service.py
requirements/base.txt (with pinned versions)
requirements/advanced.txt (with section comments)
```

### Bad Examples ❌

```
PAYMENT_API.md                          # Should be in docs/api/
test_auth.py                            # Should have timestamp
tests/test_auth.py                      # Should be in tests/api/ with timestamp
requirements/redis.txt                  # Should be in advanced.txt with comments
requirements.txt (adding new deps)      # Deprecated, use base or advanced
```

---

## 8. Migration Guide

### Migrating Existing Files

**Documentation:**
```bash
# Move to appropriate subfolder
mv SOME_DOC.md docs/api/
mv DEPLOYMENT_NOTES.md docs/deployment/
mv USER_GUIDE.md docs/guides/
```

**Tests:**
```bash
# Rename with timestamp and move to module folder
TIMESTAMP=$(date +"%y%m%d_%H%M")
mv tests/test_auth.py tests/api/${TIMESTAMP}_test_auth_endpoints.py
```

**Requirements:**
```bash
# Split into base and advanced
# 1. Identify core dependencies → base.txt
# 2. Identify optional dependencies → advanced.txt with section comments
# 3. Keep requirements.txt for backward compatibility (deprecated)
```

---

## 9. Questions & Support

If you're unsure about file placement:

1. **Documentation**: Ask "Is this API, deployment, guide, or architecture?"
2. **Tests**: Ask "Which module does this test?" (api, core, services, models, integration, unit)
3. **Requirements**: Ask "Is this required for basic functionality?" (base) or "Is this optional?" (advanced)

**When in doubt**: Create an issue or ask in pull request comments.

---

**Remember**: These requirements ensure consistency, maintainability, and ease of navigation for all developers (human and AI) working on the codebase.
