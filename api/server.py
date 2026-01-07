"""FastAPI server for employee management API."""

import sys
from contextlib import asynccontextmanager
from pathlib import Path

# Add project root to path for direct execution
sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi import FastAPI

from api.routes import router, db


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Manage database connection lifecycle."""
    db.connect()
    yield
    db.close()


app = FastAPI(
    title="Performance Review API",
    description="API for managing employee data for performance reviews",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(router)


@app.get("/", tags=["health"])
def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "performance-review-api"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("api.server:app", host="0.0.0.0", port=8000, reload=True)
