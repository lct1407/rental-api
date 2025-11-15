# CLAUDE.md Addendum - Organization Requirements

**Add this section to CLAUDE.md after "Important Notes for AI Assistants"**

---

## Project Organization Standards

### Documentation Organization

**ALL documentation files MUST be in `docs/` with subfolders:**

```
docs/
├── api/           # API documentation (BACKEND_API.md, API_DOCUMENTATION.md)
├── deployment/    # Deployment guides (DEPLOYMENT.md)
├── guides/        # User guides (STARTUP_GUIDE.md)
├── architecture/  # Architecture docs
└── project/       # Project management (IMPLEMENTATION_STATUS.md, CLAUDE_REQUIREMENTS.md)
```

**Rules:**
- ✅ Place new docs in appropriate subfolder
- ❌ Do NOT create .md files in root (except README.md, CLAUDE.md)

### Test File Organization

**ALL test files MUST follow naming: `yyMMdd_HHmm_test_<feature>.py`**

```
tests/
├── api/          # 251115_1430_test_auth_endpoints.py
├── core/         # 251115_1445_test_security.py
├── services/     # 251115_1500_test_user_service.py
├── models/       # 251115_1515_test_user_model.py
├── integration/  # 251115_1530_test_payment_flow.py
└── unit/         # 251115_1545_test_validators.py
```

**Rules:**
- ✅ Generate timestamp: `date +"%y%m%d_%H%M"`
- ✅ Place in module folder (api, core, services, models, integration, unit)
- ✅ Use format: `{timestamp}_test_{feature}.py`
- ❌ Do NOT create tests without timestamp prefix
- ❌ Do NOT place tests in root of tests/

**Example:**
```bash
TIMESTAMP=$(date +"%y%m%d_%H%M")
touch tests/api/${TIMESTAMP}_test_webhook_endpoints.py
# Result: tests/api/251115_1630_test_webhook_endpoints.py
```

### Requirements Organization

**Use TWO main files: base.txt (core) and advanced.txt (optional)**

```
requirements/
├── base.txt              # Core dependencies (FastAPI, SQLAlchemy, etc.)
├── advanced.txt          # Optional features with comment sections
├── requirements-dev.txt  # Development tools (pytest, black, mypy)
└── requirements.txt      # DEPRECATED - references base + advanced
```

**Structure:**

**base.txt** - Core dependencies required for basic functionality:
- FastAPI, Uvicorn
- SQLAlchemy, Alembic, AsyncPG
- Pydantic
- Authentication (JWT, bcrypt)
- Configuration (dotenv)

**advanced.txt** - Organized by feature with comment sections:
- REDIS - Caching and rate limiting
- AUTHENTICATION - 2FA, phone validation
- BACKGROUND TASKS - Celery
- EMAIL - Email sending
- PAYMENTS - Stripe, PayPal
- STORAGE - AWS S3
- WEBSOCKET - Real-time
- MONITORING - Prometheus, logging
- REPORTING - PDF, data processing
- UTILITIES - Additional tools

**requirements-dev.txt** - Development tools:
- TESTING - pytest, coverage
- CODE QUALITY - black, flake8, mypy
- TYPE STUBS - types-*
- DEVELOPMENT TOOLS - ipython, ipdb
- LOAD TESTING - locust
- DOCUMENTATION - mkdocs

**Installation:**

```bash
# Minimal (base only)
pip install -r requirements/base.txt

# Full production
pip install -r requirements/base.txt
pip install -r requirements/advanced.txt

# Development
pip install -r requirements/base.txt
pip install -r requirements/advanced.txt
pip install -r requirements/requirements-dev.txt

# Legacy (backward compatibility)
pip install -r requirements/requirements.txt  # references base + advanced
```

**Rules:**
- ✅ Add core dependencies to base.txt
- ✅ Add optional features to advanced.txt with section comments
- ✅ Add dev tools to requirements-dev.txt
- ✅ Pin all versions (fastapi==0.109.0)
- ❌ Do NOT modify requirements.txt directly (it's deprecated)
- ❌ Do NOT use unpinned versions (fastapi>=0.109.0)

### Quick Reference

| Task | Action |
|------|--------|
| Add API documentation | Create in `docs/api/` |
| Add deployment guide | Create in `docs/deployment/` |
| Add user guide | Create in `docs/guides/` |
| Create API test | `tests/api/{timestamp}_test_{feature}.py` |
| Create service test | `tests/services/{timestamp}_test_{feature}.py` |
| Add core dependency | Add to `requirements/base.txt` |
| Add optional feature | Add to `requirements/advanced.txt` with section comment |
| Add dev tool | Add to `requirements/requirements-dev.txt` |

### File Organization Summary

```
rental-api/
├── app/                   # Backend code
├── client/                # Frontend code
├── docs/                  # ALL documentation
│   ├── api/
│   ├── deployment/
│   ├── guides/
│   ├── architecture/
│   └── project/
├── migrations/            # Database migrations
├── requirements/          # Python dependencies
│   ├── base.txt          # Core (required)
│   ├── advanced.txt      # Features (optional)
│   ├── requirements-dev.txt  # Development
│   └── requirements.txt  # Deprecated (backward compatibility)
├── scripts/               # Utility scripts
├── tests/                 # Tests with timestamps
│   ├── api/              # {yyMMdd_HHmm}_test_*.py
│   ├── core/
│   ├── services/
│   ├── models/
│   ├── integration/
│   └── unit/
├── CLAUDE.md             # AI assistant guide
└── README.md             # Project README
```

### Pre-Commit Checklist

Before committing, verify:

**Documentation:**
- [ ] All docs in `docs/` subfolder (not root)
- [ ] Appropriate subfolder (api, deployment, guides, architecture, project)

**Tests:**
- [ ] Test files have timestamp prefix (`yyMMdd_HHmm_`)
- [ ] Tests in correct module folder
- [ ] Descriptive name after timestamp

**Requirements:**
- [ ] Dependencies in correct file (base, advanced, or dev)
- [ ] Versions pinned with `==`
- [ ] Section comments added (for advanced.txt)
- [ ] Tested in clean environment

**General:**
- [ ] No files in wrong locations
- [ ] Naming conventions followed
- [ ] Related files grouped together

### Common Mistakes to Avoid

❌ **Bad:**
```
DEPLOYMENT.md                          # Should be in docs/deployment/
test_auth.py                           # Missing timestamp
tests/test_user.py                     # Missing timestamp and folder
requirements/redis.txt                 # Should be section in advanced.txt
pip install fastapi                    # Unpinned version
```

✅ **Good:**
```
docs/deployment/DEPLOYMENT.md
tests/api/251115_1430_test_auth_endpoints.py
tests/services/251115_1445_test_user_service.py
requirements/advanced.txt              # Contains REDIS section
pip install -r requirements/base.txt
```

### Detailed Documentation

For complete details, see:
- **Documentation standards**: `docs/project/CLAUDE_REQUIREMENTS.md`
- **Test organization**: `tests/README.md`
- **Requirements guide**: `requirements/README.md`

---

**Remember:** These standards ensure consistency and maintainability across the entire codebase.
