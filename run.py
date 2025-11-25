#!/usr/bin/env python3
"""
FastAPI Application Launcher
Start the API server with uvicorn
"""
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import uvicorn
from app.config import settings


def main():
    """Run the FastAPI application"""
    print("=" * 60)
    print(f"Starting {settings.APP_NAME}")
    print(f"Environment: {settings.ENVIRONMENT}")
    print(f"Debug Mode: {settings.DEBUG}")
    print("=" * 60)
    print()
    print(f"API Server: http://0.0.0.0:{settings.PORT}")
    print(f"Swagger UI: http://localhost:{settings.PORT}/docs")
    print(f"ReDoc: http://localhost:{settings.PORT}/redoc")
    print(f"Health Check: http://localhost:{settings.PORT}/health")
    print()

    # Windows doesn't support multiple workers well, use 1 worker
    workers = 1 if sys.platform == "win32" else (1 if settings.DEBUG else 4)

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=settings.PORT,
        reload=settings.DEBUG,
        workers=workers,
        log_level="debug" if settings.DEBUG else "info",
    )


if __name__ == "__main__":
    main()
