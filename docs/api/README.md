# API Documentation

This directory contains auto-generated API documentation for the Rental API platform.

## 📚 Available Documentation Formats

- **[index.html](index.html)** - Documentation homepage with links to all formats
- **[swagger.html](swagger.html)** - Interactive Swagger UI documentation
- **[redoc.html](redoc.html)** - Beautiful ReDoc documentation
- **[openapi.json](openapi.json)** - OpenAPI 3.1.0 specification (JSON format)

## 🔄 Auto-Generation

Documentation is automatically regenerated when:

1. **On Git Commit** (via pre-commit hook)
   - Detects changes in `app/api/`, `app/schemas/`, or `app/core/openapi_config.py`
   - Runs `scripts/generate_api_docs.py`
   - Stages updated documentation files

2. **On GitHub Push** (via GitHub Actions)
   - Triggers on push to `main` or `production` branches
   - Generates docs and commits them back to the repository
   - Deploys to GitHub Pages (if configured)

3. **Manually**
   ```bash
   python scripts/generate_api_docs.py
   ```

## 🚀 Viewing Documentation Locally

### Option 1: Open Files Directly
Simply open `index.html` in your browser:
```bash
# Linux/WSL
xdg-open docs/api/index.html

# macOS
open docs/api/index.html

# Windows
start docs/api/index.html
```

### Option 2: Run Local Server
```bash
# Using Python
python -m http.server 8080 -d docs/api

# Then visit: http://localhost:8080
```

### Option 3: Use FastAPI Server
The main FastAPI application serves these files at:
- **Index**: http://localhost:8000/api-docs/
- **Swagger**: http://localhost:8000/api-docs/swagger
- **ReDoc**: http://localhost:8000/api-docs/redoc
- **OpenAPI JSON**: http://localhost:8000/api-docs/openapi.json

## 🛠️ Setup Git Hooks

To enable automatic documentation generation on commit:

```bash
# Option 1: Configure git to use .githooks directory
git config core.hooksPath .githooks

# Option 2: Copy hook to .git/hooks directory
cp .githooks/pre-commit .git/hooks/pre-commit
chmod +x .git/hooks/pre-commit
```

## 📦 Integration with UI Project

The UI project can consume the API documentation in several ways:

### 1. Direct OpenAPI JSON Import
```typescript
// In your UI project
const apiSpec = await fetch('http://localhost:8000/api-docs/openapi.json');
const openApiSchema = await apiSpec.json();
```

### 2. Use for Code Generation
```bash
# Generate TypeScript client
npx @openapitools/openapi-generator-cli generate \
  -i http://localhost:8000/api-docs/openapi.json \
  -g typescript-axios \
  -o src/api/generated
```

### 3. Embed Documentation
```html
<!-- Embed Swagger UI in your app -->
<iframe src="http://localhost:8000/api-docs/swagger" width="100%" height="800"></iframe>
```

## 🎨 Customization

To customize the documentation:

1. **Update OpenAPI Metadata**
   - Edit `app/core/openapi_config.py`
   - Modify title, description, contact info, etc.

2. **Customize HTML Templates**
   - Edit `scripts/generate_api_docs.py`
   - Modify the HTML templates in `generate_swagger_html()`, `generate_redoc_html()`, or `generate_docs_index()`

3. **Add Custom CSS/JS**
   - Add styling in the `<style>` tags
   - Include additional JavaScript libraries

## 📝 Version Control

Generated documentation files are tracked in git to ensure:
- Documentation stays in sync with code
- Easy comparison between versions
- No build step required to view docs
- Works offline

## 🔗 Related Files

- **Generator Script**: `scripts/generate_api_docs.py`
- **OpenAPI Config**: `app/core/openapi_config.py`
- **GitHub Workflow**: `.github/workflows/generate-docs.yml`
- **Pre-commit Hook**: `.githooks/pre-commit`

## 📄 License

Same license as the main project.
