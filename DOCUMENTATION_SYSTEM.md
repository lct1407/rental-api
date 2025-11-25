# 📚 API Documentation System

## Overview

The Rental API now features an **automatic documentation generation system** that builds and serves static ReDoc and Swagger UI documentation files that always stay in sync with your API code.

## ✨ Features

### 1. **Static Documentation Files**
- Pre-built HTML files that bypass rate limiting and middleware
- No runtime OpenAPI schema generation
- Fast loading and better performance
- Works offline

### 2. **Multiple Documentation Formats**
- **Swagger UI** - Interactive API explorer
- **ReDoc** - Beautiful three-panel documentation
- **OpenAPI JSON** - Raw specification file
- **Index Page** - Beautiful landing page

### 3. **Automatic Updates**
Documentation automatically regenerates when:
- You commit API changes (via git pre-commit hook)
- You push to GitHub (via GitHub Actions)
- You manually run the generator script

## 🌐 Access Documentation

### Live Server Endpoints
When your FastAPI server is running, access documentation at:

| Format | URL | Description |
|--------|-----|-------------|
| **Index** | http://localhost:8000/api-docs/ | Documentation homepage |
| **Swagger UI** | http://localhost:8000/api-docs/swagger | Interactive API explorer |
| **ReDoc** | http://localhost:8000/api-docs/redoc | Three-panel documentation |
| **OpenAPI JSON** | http://localhost:8000/api-docs/openapi.json | Raw specification (CORS enabled) |

### Static Files
Documentation files are stored in `/docs/api/`:
- `index.html` - Documentation homepage
- `swagger.html` - Swagger UI page
- `redoc.html` - ReDoc page
- `openapi.json` - OpenAPI 3.1.0 specification

## 🔨 Generate Documentation

### Manual Generation
```bash
# Generate all documentation files
python scripts/generate_api_docs.py
```

This creates:
```
docs/api/
├── index.html        # Beautiful homepage
├── swagger.html      # Swagger UI
├── redoc.html        # ReDoc
├── openapi.json      # OpenAPI spec
└── README.md         # Documentation guide
```

### Automatic Generation

#### Option 1: Git Pre-commit Hook
Automatically generates docs when you commit API changes:

```bash
# Configure git to use custom hooks directory
git config core.hooksPath .githooks

# The hook activates when you commit changes to:
# - app/api/**/*.py
# - app/schemas/**/*.py
# - app/core/openapi_config.py
```

#### Option 2: GitHub Actions
Automatically generates and commits docs on push to `main` or `production`:

The workflow (`.github/workflows/generate-docs.yml`):
1. Detects API file changes
2. Generates documentation
3. Commits updated docs back to repository
4. Optionally deploys to GitHub Pages

## 📦 Integration with UI Project

### 1. Direct OpenAPI JSON Fetch
```typescript
// Fetch the OpenAPI specification
const response = await fetch('http://localhost:8000/api-docs/openapi.json');
const openApiSpec = await response.json();

// Use for validation, type generation, etc.
```

### 2. Generate TypeScript Client
```bash
# Using OpenAPI Generator
npx @openapitools/openapi-generator-cli generate \
  -i http://localhost:8000/api-docs/openapi.json \
  -g typescript-axios \
  -o src/api/generated

# Using OpenAPI TypeScript
npx openapi-typescript http://localhost:8000/api-docs/openapi.json \
  -o src/api/schema.ts
```

### 3. Embed Documentation in UI
```html
<!-- Embed Swagger UI -->
<iframe
  src="http://localhost:8000/api-docs/swagger"
  width="100%"
  height="800"
  style="border: none;"
></iframe>

<!-- Embed ReDoc -->
<iframe
  src="http://localhost:8000/api-docs/redoc"
  width="100%"
  height="800"
  style="border: none;"
></iframe>
```

### 4. React Integration Example
```typescript
import SwaggerUI from "swagger-ui-react";
import "swagger-ui-react/swagger-ui.css";

export function ApiDocs() {
  return (
    <SwaggerUI
      url="http://localhost:8000/api-docs/openapi.json"
      docExpansion="list"
      defaultModelsExpandDepth={1}
    />
  );
}
```

## 🎨 Customization

### Update API Information
Edit `app/core/openapi_config.py`:
```python
def get_openapi_metadata():
    return {
        "title": "Your API Name",
        "description": "Your API description",
        "version": "1.0.0",
        "contact": {
            "name": "Your Name",
            "email": "your@email.com"
        }
    }
```

### Customize Documentation Templates
Edit `scripts/generate_api_docs.py`:
- Modify `generate_swagger_html()` for Swagger UI customization
- Modify `generate_redoc_html()` for ReDoc customization
- Modify `generate_docs_index()` for homepage customization

### Add Custom Styling
Documentation templates include `<style>` tags where you can add custom CSS.

## 🔧 Technical Details

### How It Works
1. **Generation Script** (`scripts/generate_api_docs.py`):
   - Imports your FastAPI app
   - Uses `get_openapi()` to generate the schema
   - Applies custom transformations
   - Saves JSON + HTML files

2. **Static File Serving** (`app/main.py:315-346`):
   - Mounts `/docs/api` directory as static files
   - Serves HTML files via `FileResponse`
   - No rate limiting or authentication required
   - CORS enabled for OpenAPI JSON

3. **FastAPI Integration**:
   - Original `/docs` and `/redoc` still work (with rate limiting)
   - New `/api-docs/*` endpoints serve static files
   - Both systems coexist independently

### Files Structure
```
rental-api/
├── app/
│   ├── main.py              # Static file serving (lines 315-346)
│   └── core/
│       └── openapi_config.py # OpenAPI customization
├── scripts/
│   └── generate_api_docs.py  # Documentation generator
├── docs/
│   └── api/                   # Generated documentation
│       ├── index.html
│       ├── swagger.html
│       ├── redoc.html
│       ├── openapi.json
│       └── README.md
├── .github/
│   └── workflows/
│       └── generate-docs.yml  # CI/CD automation
└── .githooks/
    └── pre-commit             # Git hook for auto-generation
```

## 🚀 Deployment

### Production Deployment
1. Generate docs before deployment:
   ```bash
   python scripts/generate_api_docs.py
   ```

2. Commit generated files:
   ```bash
   git add docs/api/
   git commit -m "docs: Update API documentation"
   ```

3. Deploy with documentation included

### GitHub Pages (Optional)
The GitHub Actions workflow can automatically deploy documentation to GitHub Pages:

1. Enable GitHub Pages in repository settings
2. Set source to "GitHub Actions"
3. Push to main branch
4. Documentation will be available at `https://your-username.github.io/rental-api/api/`

## 🎯 Benefits

### For Developers
- **Always Up-to-Date**: Docs regenerate automatically
- **No Manual Work**: Set it and forget it
- **Version Controlled**: Docs tracked in git
- **Offline Access**: Works without running the server

### For API Consumers
- **Fast Loading**: Pre-built static files
- **No Rate Limits**: Documentation bypasses rate limiting
- **Multiple Formats**: Choose your preferred format
- **Beautiful UI**: Modern, responsive design

### For CI/CD
- **Automated**: Integrates with GitHub Actions
- **Consistent**: Same docs in all environments
- **Testable**: Can verify docs in CI pipeline

## 📊 Comparison: Static vs Dynamic

| Feature | Static Docs (/api-docs/*) | Dynamic Docs (/docs, /redoc) |
|---------|---------------------------|-------------------------------|
| **Rate Limiting** | ❌ No | ✅ Yes |
| **Load Time** | ⚡ Fast (pre-built) | 🐢 Slower (runtime generation) |
| **Offline** | ✅ Yes | ❌ No |
| **CORS** | ✅ Enabled | ⚠️ Limited |
| **Customization** | ✅ Full control | ⚠️ FastAPI defaults |
| **Updates** | 🔄 Manual/Automated | 🔄 Automatic |

**Recommendation**: Use static docs (`/api-docs/*`) for production and UI integration.

## 🔍 Troubleshooting

### Documentation Not Updating
```bash
# Regenerate manually
python scripts/generate_api_docs.py

# Check if files were created
ls -la docs/api/

# Restart FastAPI server
pkill -f uvicorn
uvicorn app.main:app --reload
```

### Git Hook Not Working
```bash
# Ensure hook is executable
chmod +x .githooks/pre-commit

# Configure git to use custom hooks
git config core.hooksPath .githooks

# Test the hook
.githooks/pre-commit
```

### OpenAPI JSON Shows Error
```bash
# Clear Redis cache
redis-cli FLUSHALL

# Regenerate documentation
python scripts/generate_api_docs.py

# Check file permissions
ls -la docs/api/openapi.json
```

## 📖 Additional Resources

- **OpenAPI Specification**: https://spec.openapis.org/oas/v3.1.0
- **Swagger UI**: https://swagger.io/tools/swagger-ui/
- **ReDoc**: https://redocly.com/docs/redoc/
- **FastAPI Docs**: https://fastapi.tiangolo.com/advanced/extending-openapi/

## 🎉 Summary

You now have a **professional, automated API documentation system** that:
- ✅ Generates beautiful Swagger and ReDoc documentation
- ✅ Serves static files (no rate limiting issues)
- ✅ Auto-updates on code changes (git hooks + GitHub Actions)
- ✅ Provides OpenAPI JSON for UI integration
- ✅ Works offline and loads fast
- ✅ Fully customizable

**For UI Project**: Use `http://localhost:8000/api-docs/openapi.json` to fetch the API specification!
