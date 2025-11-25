"""
Generate Static API Documentation
Generates OpenAPI JSON, Swagger UI, and ReDoc HTML files
"""
import json
import sys
import io
from pathlib import Path

# Fix Windows console encoding for emojis
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

from fastapi.openapi.utils import get_openapi

# Import the FastAPI app
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.main import app
from app.core.openapi_config import customize_openapi_schema


def generate_openapi_json(output_path: Path):
    """Generate OpenAPI JSON schema"""
    print("📄 Generating OpenAPI JSON schema...")

    # Generate OpenAPI schema
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        openapi_version=app.openapi_version,
        description=app.description,
        terms_of_service=app.terms_of_service,
        contact=app.contact,
        license_info=app.license_info,
        routes=app.routes,
        tags=app.openapi_tags,
        servers=app.servers,
    )

    # Customize the schema
    customized_schema = customize_openapi_schema(openapi_schema)

    # Write to file
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(customized_schema, f, indent=2, ensure_ascii=False)

    print(f"✅ OpenAPI JSON saved to: {output_path}")
    return customized_schema


def generate_swagger_html(openapi_json_url: str, output_path: Path):
    """Generate static Swagger UI HTML"""
    print("📝 Generating Swagger UI HTML...")

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>API Documentation - Swagger UI</title>
    <link rel="stylesheet" type="text/css" href="https://unpkg.com/swagger-ui-dist@5.11.0/swagger-ui.css">
    <link rel="icon" type="image/png" href="https://fastapi.tiangolo.com/img/favicon.png">
    <style>
        body {{
            margin: 0;
            padding: 0;
        }}
    </style>
</head>
<body>
    <div id="swagger-ui"></div>
    <script src="https://unpkg.com/swagger-ui-dist@5.11.0/swagger-ui-bundle.js"></script>
    <script src="https://unpkg.com/swagger-ui-dist@5.11.0/swagger-ui-standalone-preset.js"></script>
    <script>
        window.onload = function() {{
            const ui = SwaggerUIBundle({{
                url: '{openapi_json_url}',
                dom_id: '#swagger-ui',
                deepLinking: true,
                presets: [
                    SwaggerUIBundle.presets.apis,
                    SwaggerUIStandalonePreset
                ],
                plugins: [
                    SwaggerUIBundle.plugins.DownloadUrl
                ],
                layout: "StandaloneLayout",
                defaultModelsExpandDepth: 1,
                defaultModelExpandDepth: 1,
                docExpansion: "list",
                filter: true,
                showRequestHeaders: true,
                tryItOutEnabled: true
            }});
            window.ui = ui;
        }};
    </script>
</body>
</html>"""

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_content)

    print(f"✅ Swagger UI HTML saved to: {output_path}")


def generate_redoc_html(openapi_json_url: str, output_path: Path):
    """Generate static ReDoc HTML"""
    print("📘 Generating ReDoc HTML...")

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>API Documentation - ReDoc</title>
    <link rel="icon" type="image/png" href="https://fastapi.tiangolo.com/img/favicon.png">
    <style>
        body {{
            margin: 0;
            padding: 0;
        }}
    </style>
</head>
<body>
    <redoc spec-url='{openapi_json_url}'></redoc>
    <script src="https://cdn.redoc.ly/redoc/latest/bundles/redoc.standalone.js"></script>
</body>
</html>"""

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_content)

    print(f"✅ ReDoc HTML saved to: {output_path}")


def generate_docs_index(output_path: Path):
    """Generate index page for API documentation"""
    print("🏠 Generating documentation index...")

    html_content = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>API Documentation</title>
    <link rel="icon" type="image/png" href="https://fastapi.tiangolo.com/img/favicon.png">
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
        }
        .container {
            background: white;
            border-radius: 20px;
            padding: 60px 40px;
            max-width: 800px;
            width: 100%;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
        }
        h1 {
            color: #2d3748;
            font-size: 2.5rem;
            margin-bottom: 10px;
            text-align: center;
        }
        .subtitle {
            color: #718096;
            font-size: 1.1rem;
            text-align: center;
            margin-bottom: 40px;
        }
        .version {
            display: inline-block;
            background: #667eea;
            color: white;
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 0.85rem;
            font-weight: 600;
            margin-left: 10px;
        }
        .cards {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 40px;
        }
        .card {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-radius: 15px;
            padding: 30px;
            text-decoration: none;
            color: white;
            transition: transform 0.3s, box-shadow 0.3s;
            display: flex;
            flex-direction: column;
            align-items: center;
            text-align: center;
        }
        .card:hover {
            transform: translateY(-5px);
            box-shadow: 0 10px 30px rgba(102, 126, 234, 0.4);
        }
        .card-icon {
            font-size: 3rem;
            margin-bottom: 15px;
        }
        .card-title {
            font-size: 1.5rem;
            font-weight: 600;
            margin-bottom: 10px;
        }
        .card-description {
            font-size: 0.95rem;
            opacity: 0.9;
        }
        .info {
            background: #f7fafc;
            border-left: 4px solid #667eea;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 20px;
        }
        .info h3 {
            color: #2d3748;
            font-size: 1.2rem;
            margin-bottom: 10px;
        }
        .info p {
            color: #4a5568;
            line-height: 1.6;
        }
        .info code {
            background: #edf2f7;
            padding: 2px 6px;
            border-radius: 4px;
            font-family: 'Courier New', monospace;
            color: #667eea;
        }
        .footer {
            text-align: center;
            color: #718096;
            font-size: 0.9rem;
            margin-top: 30px;
            padding-top: 20px;
            border-top: 1px solid #e2e8f0;
        }
        @media (max-width: 600px) {
            .container {
                padding: 40px 20px;
            }
            h1 {
                font-size: 2rem;
            }
            .cards {
                grid-template-columns: 1fr;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🚀 API Documentation <span class="version">v2.0.0</span></h1>
        <p class="subtitle">Enterprise API Management Platform</p>

        <div class="info">
            <h3>📖 Quick Start</h3>
            <p>Choose your preferred documentation format below. All versions are automatically generated from the OpenAPI specification.</p>
        </div>

        <div class="cards">
            <a href="swagger.html" class="card">
                <div class="card-icon">📝</div>
                <div class="card-title">Swagger UI</div>
                <div class="card-description">Interactive API explorer with try-it-out functionality</div>
            </a>

            <a href="redoc.html" class="card">
                <div class="card-icon">📘</div>
                <div class="card-title">ReDoc</div>
                <div class="card-description">Beautiful three-panel documentation</div>
            </a>

            <a href="openapi.json" class="card" download>
                <div class="card-icon">📄</div>
                <div class="card-title">OpenAPI JSON</div>
                <div class="card-description">Raw OpenAPI 3.1.0 specification</div>
            </a>
        </div>

        <div class="info">
            <h3>🔐 Authentication</h3>
            <p>Most endpoints require JWT authentication. Include your token in the Authorization header: <code>Bearer &lt;your_token&gt;</code></p>
        </div>

        <div class="info">
            <h3>🌐 Base URL</h3>
            <p>All API endpoints are prefixed with: <code>/api/v1</code></p>
        </div>

        <div class="footer">
            <p>Powered by FastAPI | Generated automatically from OpenAPI specification</p>
        </div>
    </div>
</body>
</html>"""

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_content)

    print(f"✅ Documentation index saved to: {output_path}")


def main():
    """Main function to generate all documentation"""
    print("=" * 80)
    print("🔨 GENERATING API DOCUMENTATION")
    print("=" * 80)
    print()

    # Setup paths
    docs_dir = Path(__file__).parent.parent / "docs" / "api"
    docs_dir.mkdir(parents=True, exist_ok=True)

    openapi_json_path = docs_dir / "openapi.json"
    swagger_html_path = docs_dir / "swagger.html"
    redoc_html_path = docs_dir / "redoc.html"
    index_html_path = docs_dir / "index.html"

    # Generate OpenAPI JSON
    generate_openapi_json(openapi_json_path)
    print()

    # Generate Swagger UI HTML
    generate_swagger_html("./openapi.json", swagger_html_path)
    print()

    # Generate ReDoc HTML
    generate_redoc_html("./openapi.json", redoc_html_path)
    print()

    # Generate index page
    generate_docs_index(index_html_path)
    print()

    print("=" * 80)
    print("✅ DOCUMENTATION GENERATION COMPLETE!")
    print("=" * 80)
    print()
    print("📂 Files generated:")
    print(f"   • {openapi_json_path}")
    print(f"   • {swagger_html_path}")
    print(f"   • {redoc_html_path}")
    print(f"   • {index_html_path}")
    print()
    print("🌐 View documentation:")
    print(f"   • Open file://{index_html_path.absolute()}")
    print(f"   • Or serve with: python -m http.server 8080 -d {docs_dir}")
    print()


if __name__ == "__main__":
    main()
