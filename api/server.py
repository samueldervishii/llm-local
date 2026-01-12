"""FastAPI server for employee management API."""

import sys
from contextlib import asynccontextmanager
from pathlib import Path

# Add project root to path for direct execution
sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi import FastAPI

from logging_config import setup_logging, get_logger
from api.routes import router, db
from api.generate_routes import router as generate_router, init_services
from api.template_routes import router as template_router, init_db as init_template_db
from api.review_routes import router as review_router, init_db as init_review_db
from api.bulk_routes import router as bulk_router, init_db as init_bulk_db
from api.stats_routes import router as stats_router, init_db as init_stats_db
from llm import LocalLLM

# Initialize logging
setup_logging()
logger = get_logger(__name__)

API_VERSION = "2.1.0"
API_PREFIX = "/api/v2"

# LLM instance (loaded on startup)
llm_instance: LocalLLM = None


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Manage application lifecycle - database and LLM."""
    global llm_instance

    logger.info("Starting HR Document Generator API...")

    # Connect to database
    logger.info("Connecting to MongoDB...")
    db.connect()
    logger.info("MongoDB connected successfully")

    # Load LLM model
    logger.info("Loading LLM model (this may take a moment)...")
    llm_instance = LocalLLM()
    llm_instance.load()
    logger.info("LLM model loaded successfully")

    # Initialize generation services
    init_services(llm_instance, db)
    init_template_db(db)
    init_review_db(db)
    init_bulk_db(db)
    init_stats_db(db)
    logger.info("All services initialized")

    logger.info("API startup complete - ready to serve requests")

    yield

    # Cleanup
    logger.info("Shutting down API...")
    if llm_instance:
        llm_instance.unload()
        logger.info("LLM model unloaded")
    db.close()
    logger.info("MongoDB connection closed")
    logger.info("Shutdown complete")


app = FastAPI(
    title="HR Document Generator API",
    description="API for managing employee data and generating performance reviews and onboarding plans",
    version=API_VERSION,
    lifespan=lifespan,
    docs_url=f"{API_PREFIX}/docs",
    redoc_url=f"{API_PREFIX}/redoc",
    openapi_url=f"{API_PREFIX}/openapi.json",
)

# Include routers
app.include_router(router, prefix=API_PREFIX)
app.include_router(generate_router, prefix=API_PREFIX)
app.include_router(template_router, prefix=API_PREFIX)
app.include_router(review_router, prefix=API_PREFIX)
app.include_router(bulk_router, prefix=API_PREFIX)
app.include_router(stats_router, prefix=API_PREFIX)


@app.get("/", tags=["health"])
def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "hr-document-generator",
        "version": API_VERSION,
        "api": API_PREFIX,
        "llm_loaded": llm_instance is not None
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
    import argparse
    import uvicorn

    parser = argparse.ArgumentParser(description="HR Document Generator API")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload (dev mode)")
    parser.add_argument("--port", type=int, default=8000, help="Port to run on")
    args = parser.parse_args()

    print(BANNER)

    if args.reload:
        logger.warning("Running in development mode with auto-reload")

    uvicorn.run(
        "api.server:app",
        host="0.0.0.0",
        port=args.port,
        reload=args.reload,
    )
