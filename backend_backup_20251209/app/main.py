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
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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
    db: Session = Depends(database.get_db)
):
    """Получить список грузов"""
    query = db.query(models.Freight)
    
    if not show_hidden:
        query = query.filter(models.Freight.is_hidden == False)
    
    freights = query.order_by(models.Freight.created_at.desc()).offset(skip).limit(limit).all()
    return freights


@app.get("/freights/{freight_id}", response_model=schemas.FreightResponse)
def get_freight(freight_id: int, db: Session = Depends(database.get_db)):
    """Получить груз по ID"""
    freight = db.query(models.Freight).filter(models.Freight.id == freight_id).first()
    if not freight:
        raise HTTPException(status_code=404, detail="Freight not found")
    return freight


@app.patch("/freights/{freight_id}", response_model=schemas.FreightResponse)
def update_freight(
    freight_id: int,
    freight_update: schemas.FreightUpdate,
    db: Session = Depends(database.get_db)
):
    """Обновить груз (скрыть, пометить как сделку, установить ставки)"""
    freight = db.query(models.Freight).filter(models.Freight.id == freight_id).first()
    if not freight:
        raise HTTPException(status_code=404, detail="Freight not found")
    
    # Update only provided fields
    update_data = freight_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(freight, field, value)
    
    freight.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(freight)
    return freight


@app.delete("/freights/{freight_id}")
def delete_freight(freight_id: int, db: Session = Depends(database.get_db)):
    """Удалить груз"""
    freight = db.query(models.Freight).filter(models.Freight.id == freight_id).first()
    if not freight:
        raise HTTPException(status_code=404, detail="Freight not found")
    
    db.delete(freight)
    db.commit()
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
def get_trucks(db: Session = Depends(database.get_db)):
    """Get all trucks"""
    trucks = db.query(models.Truck).filter(models.Truck.is_active == True).all()
    return trucks

@app.get("/trucks/{truck_id}", response_model=schemas.TruckResponse)
def get_truck(truck_id: int, db: Session = Depends(database.get_db)):
    """Get truck by ID"""
    truck = db.query(models.Truck).filter(models.Truck.id == truck_id).first()
    if not truck:
        raise HTTPException(status_code=404, detail="Truck not found")
    return truck

@app.post("/trucks", response_model=schemas.TruckResponse)
def create_truck(truck: schemas.TruckCreate, db: Session = Depends(database.get_db)):
    """Create a new truck"""
    db_truck = models.Truck(**truck.model_dump())
    db.add(db_truck)
    db.commit()
    db.refresh(db_truck)
    return db_truck

@app.patch("/trucks/{truck_id}", response_model=schemas.TruckResponse)
def update_truck(
    truck_id: int,
    truck_update: schemas.TruckUpdate,
    db: Session = Depends(database.get_db)
):
    """Update truck details"""
    truck = db.query(models.Truck).filter(models.Truck.id == truck_id).first()
    if not truck:
        raise HTTPException(status_code=404, detail="Truck not found")
    
    update_data = truck_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(truck, field, value)
    
    truck.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(truck)
    return truck

@app.delete("/trucks/{truck_id}")
def delete_truck(truck_id: int, db: Session = Depends(database.get_db)):
    """Delete (deactivate) a truck"""
    truck = db.query(models.Truck).filter(models.Truck.id == truck_id).first()
    if not truck:
        raise HTTPException(status_code=404, detail="Truck not found")
    
    truck.is_active = False
    db.commit()
    return {"message": "Truck deactivated successfully"}

@app.post("/trucks/{truck_id}/update-gps")
async def update_truck_gps(truck_id: int, db: Session = Depends(database.get_db)):
    """Update truck GPS location from GPS Dozor"""
    from .services.gps_service import GpsDozorService
    from .services.google_maps import GoogleMapsService
    
    truck = db.query(models.Truck).filter(models.Truck.id == truck_id).first()
    if not truck:
        raise HTTPException(status_code=404, detail="Truck not found")
    
    if not truck.gps_vehicle_code:
        raise HTTPException(status_code=400, detail="GPS vehicle code not set for this truck")
    
    gps_service = GpsDozorService()
    maps_service = GoogleMapsService()
    
    if not gps_service.is_configured():
        raise HTTPException(status_code=500, detail="GPS Dozor credentials not configured")
    
    try:
        # Get GPS coordinates
        coords = gps_service.get_vehicle_location(truck.gps_vehicle_code)
        if not coords:
            raise HTTPException(status_code=404, detail="Could not get GPS location for this vehicle")
        
        lat, lng = coords
        truck.last_known_lat = lat
        truck.last_known_lng = lng
        
        # Get formatted address in the desired format: CC, ZIP, City
        addr_data = maps_service.reverse_geocode_structured(lat, lng)
        
        location_parts = []
        if addr_data and addr_data.get("country_code"):
            location_parts.append(addr_data["country_code"])
            if addr_data.get("postal_code"):
                location_parts.append(addr_data["postal_code"])
            if addr_data.get("city"):
                location_parts.append(addr_data["city"])
        
        if location_parts:
            truck.last_known_location = ", ".join(location_parts)
        else:
            # Fallback to general reverse geocode if structured data is insufficient
            address = maps_service.reverse_geocode(lat, lng)
            truck.last_known_location = address if address else f"{lat}, {lng}"
        
        truck.gps_updated_at = datetime.utcnow()
        db.commit()
        db.refresh(truck)
        
        return {
            "success": True,
            "location": truck.last_known_location,
            "coordinates": {"lat": lat, "lng": lng},
            "updated_at": truck.gps_updated_at
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"GPS update failed: {str(e)}")


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
