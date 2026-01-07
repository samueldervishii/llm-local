"""FastAPI server for employee management API."""

import sys
from contextlib import asynccontextmanager
from pathlib import Path

# Add project root to path for direct execution
sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi import FastAPI

from api.routes import router, db

API_VERSION = "1.0.0"
API_PREFIX = "/api/v1"


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Manage database connection lifecycle."""
    db.connect()
    yield
    db.close()


app = FastAPI(
    title="HR Document Generator API",
    description="API for managing employee data for performance reviews and onboarding",
    version=API_VERSION,
    lifespan=lifespan,
    docs_url=f"{API_PREFIX}/docs",
    redoc_url=f"{API_PREFIX}/redoc",
    openapi_url=f"{API_PREFIX}/openapi.json",
)

app.include_router(router, prefix=API_PREFIX)


@app.get("/", tags=["health"])
def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "hr-document-generator",
        "version": API_VERSION,
        "api": API_PREFIX
    }


BANNER = f"""
 _   _ ____     ____
| | | |  _ \\   / ___| ___ _ __
| |_| | |_) | | |  _ / _ \\ '_ \\
|  _  |  _ <  | |_| |  __/ | | |
|_| |_|_| \\_\\  \\____|\\___|_| |_|

HR Document Generator API v{API_VERSION}
API: {API_PREFIX}
Docs: http://localhost:8000{API_PREFIX}/docs
──────────────────────────────────────
"""


if __name__ == "__main__":
    import uvicorn

    print(BANNER)
    uvicorn.run("api.server:app", host="0.0.0.0", port=8000, reload=True)
