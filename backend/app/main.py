"""
Mini-TMS FastAPI Backend
Transportation Management System
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.config import settings
from app.database import engine, Base
from app.routes import trucks, freights, gps, health
from app.services.tasks import init_scheduler, shutdown_scheduler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create tables
Base.metadata.create_all(bind=engine)

# Initialize FastAPI app
app = FastAPI(
    title="Mini-TMS API",
    description="Transportation Management System",
    version="1.0.0"
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router, prefix="/api", tags=["health"])
app.include_router(trucks.router, prefix="/api", tags=["trucks"])
app.include_router(freights.router, prefix="/api", tags=["freights"])
app.include_router(gps.router, prefix="/api", tags=["gps"])


@app.on_event("startup")
async def startup_event():
    """Initialize on startup"""
    logger.info("🚀 Mini-TMS Backend starting...")
    if settings.ENABLE_BACKGROUND_TASKS:
        await init_scheduler()
        logger.info("✅ Background tasks initialized")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("🛑 Mini-TMS Backend shutting down...")
    await shutdown_scheduler()
    logger.info("✅ Background tasks stopped")


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Mini-TMS API",
        "version": "1.0.0",
        "docs": "/docs"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=True
    )
