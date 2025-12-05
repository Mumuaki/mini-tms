from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from datetime import datetime
import logging

from app.config import Settings
from app.database import engine, Base, get_db
from app.routes import trucks, freights, gps, health
from app.services.tasks import run_scraper_task

logger = logging.getLogger(__name__)
settings = Settings()

# Create tables on startup
Base.metadata.create_all(bind=engine)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 Mini-TMS Starting...")
    yield
    logger.info("🛑 Mini-TMS Shutting down...")

app = FastAPI(
    title="Mini-TMS API",
    description="Transportation Management System with Trans.eu Integration",
    version="1.0.0",
    lifespan=lifespan
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router)
app.include_router(trucks.router)
app.include_router(freights.router)
app.include_router(gps.router)

@app.get("/")
async def root():
    return {
        "service": "Mini-TMS",
        "version": "1.0.0",
        "status": "operational",
        "docs": "/docs",
        "timestamp": datetime.utcnow().isoformat()
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )

