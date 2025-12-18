<<<<<<< HEAD
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
=======
import asyncio
import sys

if sys.platform == 'win32':
    # Принудительно используем ProactorEventLoop для Windows
    # Это необходимо для работы Playwright и подпроцессов
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import List, Optional
from datetime import datetime
from . import models, database, schemas
from .services.trans_eu import TransEuScraper
from .services.tasks import run_scraper_task
from .repositories import FreightRepository
from .use_cases import FreightUseCase
from .repositories import TruckRepository
from .use_cases import TruckUseCase

models.Base.metadata.create_all(bind=database.engine)

app = FastAPI(
    title="Mini-TMS API",
    description="API для управления грузоперевозками с интеграцией Trans.eu",
    version="0.1.0"
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
>>>>>>> 97953c3 (Initial commit from Specify template)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

<<<<<<< HEAD
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
=======
# Dependency injection for repositories and use cases
def get_freight_repository(db: Session = Depends(database.get_db)) -> FreightRepository:
    """Provide FreightRepository injected with DB session."""
    return FreightRepository(db)


def get_freight_use_case(repo: FreightRepository = Depends(get_freight_repository)) -> FreightUseCase:
    """Provide FreightUseCase injected with its repository."""
    return FreightUseCase(repo)


def get_truck_repository(db: Session = Depends(database.get_db)) -> TruckRepository:
    """Provide TruckRepository injected with DB session."""
    return TruckRepository(db)


def get_truck_use_case(repo: TruckRepository = Depends(get_truck_repository)) -> TruckUseCase:
    """Provide TruckUseCase injected with its repository."""
    return TruckUseCase(repo)


# ============================================================================
# Root endpoint
# ============================================================================
@app.get("/")
def read_root():
    return {
        "message": "Mini-TMS Backend is running",
        "version": "0.1.0",
        "endpoints": {
            "freights": "/freights",
            "scrape": "/freights/scrape",
            "docs": "/docs"
        }
    }


# ============================================================================
# Freight endpoints
# ============================================================================
@app.get("/freights", response_model=List[schemas.FreightResponse])
def get_freights(
    skip: int = 0,
    limit: int = 100,
    show_hidden: bool = False,
    use_case: FreightUseCase = Depends(get_freight_use_case)
):
    """Получить список грузов через слой UseCase (пагинация и фильтрация)."""
    if show_hidden:
        freights = use_case.repository.list_all(skip=skip, limit=limit)
    else:
        freights = use_case.repository.list_active(skip=skip, limit=limit)

    return freights


@app.get("/freights/{freight_id}", response_model=schemas.FreightResponse)
def get_freight(
    freight_id: int,
    use_case: FreightUseCase = Depends(get_freight_use_case)
):
    """Получить груз по ID (через слой UseCase)."""
    freight = use_case.repository.get_by_id(freight_id)
    if not freight:
        raise HTTPException(status_code=404, detail="Freight not found")
    return freight


@app.patch("/freights/{freight_id}", response_model=schemas.FreightResponse)
def update_freight(
    freight_id: int,
    freight_update: schemas.FreightUpdate,
    use_case: FreightUseCase = Depends(get_freight_use_case)
):
    """Обновить груз — делегирует бизнес-логику в `FreightUseCase`."""
    try:
        updated = use_case.update_freight(freight_id, freight_update)
        return updated
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.delete("/freights/{freight_id}")
def delete_freight(freight_id: int, use_case: FreightUseCase = Depends(get_freight_use_case)):
    """Удалить груз — делегирует удаление в `FreightUseCase`."""
    deleted = use_case.delete_freight(freight_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Freight not found")
    return {"message": "Freight deleted successfully"}


# ============================================================================
# Scraper endpoints
# ============================================================================
@app.post("/scraper/launch")
async def launch_browser():
    """
    Запустить браузер для ручной авторизации пользователя.
    Браузер откроется на странице логина Trans.eu.
    """
    print("=" * 50)
    print("LAUNCH BROWSER ENDPOINT CALLED")
    print("=" * 50)
    
    from .services.scraper_manager import scraper_manager
    
    # Launch browser directly (not in background, but return quickly)
    try:
        print("Starting browser launch...")
        await scraper_manager.launch_browser()
        print("Browser launched successfully!")
        return {
            "success": True,
            "message": "Browser launched successfully. Please login manually."
        }
    except Exception as e:
        print(f"ERROR launching browser: {e}")
        import traceback
        traceback.print_exc()
        return {
            "success": False,
            "message": f"Failed to launch browser: {repr(e)}"
        }


@app.post("/freights/scrape")
async def scrape_freights(
    scrape_request: schemas.ScrapeRequest,
    background_tasks: BackgroundTasks
):
    """
    Запустить скрейпер Trans.eu в фоновом режиме.
    Требует, чтобы браузер был уже открыт и пользователь авторизован.
    """
    background_tasks.add_task(
        run_scraper_task,
        origin=scrape_request.origin,
        destination=scrape_request.destination,
        headless=scrape_request.headless,
        loading_date_from=scrape_request.loading_date_from,
        loading_date_to=scrape_request.loading_date_to,
        unloading_date_from=scrape_request.unloading_date_from,
        unloading_date_to=scrape_request.unloading_date_to
    )
    
    return {
        "success": True,
        "message": "Scraping started in background",
        "freights_count": 0,
        "new_freights": 0
    }


# ============================================================================
# Truck endpoints
# ============================================================================
@app.get("/trucks", response_model=List[schemas.TruckResponse])
def get_trucks(
    use_case: TruckUseCase = Depends(get_truck_use_case),
    skip: int = 0,
    limit: int = 100
):
    """Get active trucks via TruckUseCase."""
    return use_case.list_available_trucks(skip=skip, limit=limit)

@app.get("/trucks/{truck_id}", response_model=schemas.TruckResponse)
def get_truck(truck_id: int, use_case: TruckUseCase = Depends(get_truck_use_case)):
    """Get truck by ID via TruckUseCase."""
    truck = use_case.repository.get_by_id(truck_id)
    if not truck:
        raise HTTPException(status_code=404, detail="Truck not found")
    return truck

@app.post("/trucks", response_model=schemas.TruckResponse)
def create_truck(truck: schemas.TruckCreate, use_case: TruckUseCase = Depends(get_truck_use_case)):
    """Create a new truck via TruckRepository."""
    created = use_case.repository.create(truck.model_dump())
    return created

@app.patch("/trucks/{truck_id}", response_model=schemas.TruckResponse)
def update_truck(
    truck_id: int,
    truck_update: schemas.TruckUpdate,
    use_case: TruckUseCase = Depends(get_truck_use_case)
):
    """Update truck details via TruckUseCase."""
    try:
        return use_case.update_truck(truck_id, truck_update)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@app.delete("/trucks/{truck_id}")
def delete_truck(truck_id: int, use_case: TruckUseCase = Depends(get_truck_use_case)):
    """Deactivate truck via TruckUseCase."""
    try:
        use_case.deactivate_truck(truck_id)
        return {"message": "Truck deactivated successfully"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@app.post("/trucks/{truck_id}/update-gps")
async def update_truck_gps(truck_id: int, db: Session = Depends(database.get_db), use_case: TruckUseCase = Depends(get_truck_use_case)):
    """Update truck GPS location from GPS Dozor"""
    from .services.gps_service import GpsDozorService
    from .services.google_maps import GoogleMapsService
    truck = use_case.repository.get_by_id(truck_id)
    if not truck:
        raise HTTPException(status_code=404, detail="Truck not found")

    if not truck.gps_vehicle_code:
        raise HTTPException(status_code=400, detail="GPS vehicle code not set for this truck")

    gps_service = GpsDozorService()
    maps_service = GoogleMapsService()

    if not gps_service.is_configured():
        raise HTTPException(status_code=500, detail="GPS Dozor credentials not configured")

    try:
        coords = gps_service.get_vehicle_location(truck.gps_vehicle_code)
        if not coords:
            raise HTTPException(status_code=404, detail="Could not get GPS location for this vehicle")

        lat, lng = coords

        # Get formatted address
        addr_data = maps_service.reverse_geocode_structured(lat, lng)
        location_parts = []
        if addr_data and addr_data.get("country_code"):
            location_parts.append(addr_data["country_code"])
            if addr_data.get("postal_code"):
                location_parts.append(addr_data["postal_code"])
            if addr_data.get("city"):
                location_parts.append(addr_data["city"])

        if location_parts:
            formatted = ", ".join(location_parts)
        else:
            formatted = maps_service.reverse_geocode(lat, lng) or f"{lat}, {lng}"

        # Delegate update to use case
        updated = use_case.update_truck_location(truck_id, lat, lng, formatted)

        return {
            "success": True,
            "location": updated.last_known_location,
            "coordinates": {"lat": updated.last_known_lat, "lng": updated.last_known_lng},
            "updated_at": updated.gps_updated_at
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"GPS update failed: {str(e)}")


@app.get("/trucks/{truck_id}/location")
def get_truck_location(truck_id: int, use_case: TruckUseCase = Depends(get_truck_use_case)):
    """Get current real-time location of a truck.

    Attempts a live GPS fetch; if unavailable returns last known location via use case.
    """
    from .services.gps_service import GpsDozorService
    from .services.google_maps import GoogleMapsService

    truck = use_case.repository.get_by_id(truck_id)
    if not truck:
        raise HTTPException(status_code=404, detail="Truck not found")

    gps_service = GpsDozorService()
    maps_service = GoogleMapsService()

    if not truck.gps_vehicle_code:
        # Return last known if no GPS device configured
        loc = use_case.get_truck_location(truck_id)
        if not loc:
            raise HTTPException(status_code=400, detail="GPS vehicle code not set and no last known location")
        return loc

    if not gps_service.is_configured():
        # Fall back to last known
        loc = use_case.get_truck_location(truck_id)
        if loc:
            return loc
        raise HTTPException(status_code=500, detail="GPS service not configured")

    try:
        coords = gps_service.get_vehicle_location(truck.gps_vehicle_code)
        if not coords:
            # fall back to last known
            loc = use_case.get_truck_location(truck_id)
            if loc:
                return loc
            raise HTTPException(status_code=404, detail="Could not fetch live GPS data")

        lat, lng = coords
        addr_data = maps_service.reverse_geocode_structured(lat, lng)

        if addr_data and addr_data.get("country_code"):
            parts = [addr_data["country_code"]]
            if addr_data.get("postal_code"):
                parts.append(addr_data["postal_code"])
            elif addr_data.get("city"):
                parts.append(addr_data["city"])
            formatted_address = ", ".join(parts)
        else:
            formatted_address = maps_service.reverse_geocode(lat, lng) or f"{lat}, {lng}"

        return {
            "lat": lat,
            "lng": lng,
            "address": formatted_address,
            "timestamp": datetime.utcnow().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



# ============================================================================
# Health check
# ============================================================================
@app.get("/health")
def health_check(db: Session = Depends(database.get_db)):
    """Проверка состояния API и подключения к БД"""
    try:
        # Test database connection
        db.execute("SELECT 1")
        return {
            "status": "healthy",
            "database": "connected",
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "database": "disconnected",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }
>>>>>>> 97953c3 (Initial commit from Specify template)
