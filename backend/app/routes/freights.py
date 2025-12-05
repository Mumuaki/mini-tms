from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from app.database import get_db
from app.models import OffersNormalized, Truck
from app.schemas import FreightResponse, ScrapeRequest, ScrapeResponse
from app.services.transeu import TransEuScraper
from app.services.tasks import run_scraper_task
import logging

router = APIRouter(prefix="/api/freights", tags=["freights"])
logger = logging.getLogger(__name__)

@router.get("", response_model=List[FreightResponse])
async def list_freights(
    origin: Optional[str] = None,
    destination: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    query = db.query(OffersNormalized)
    
    if origin:
        query = query.filter(OffersNormalized.loadingPlace.ilike(f"%{origin}%"))
    if destination:
        query = query.filter(OffersNormalized.unloadingPlace.ilike(f"%{destination}%"))
    
    freights = query.order_by(OffersNormalized.createdAt.desc()).offset(skip).limit(limit).all()
    return freights

@router.get("/{freight_id}", response_model=FreightResponse)
async def get_freight(freight_id: int, db: Session = Depends(get_db)):
    freight = db.query(OffersNormalized).filter(OffersNormalized.id == freight_id).first()
    if not freight:
        raise HTTPException(status_code=404, detail="Freight not found")
    return freight

@router.post("/scrape", response_model=ScrapeResponse)
async def scrape_freights(
    request: ScrapeRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    # Handle GPS origin
    if not request.origin and request.truckId:
        truck = db.query(Truck).filter(Truck.id == request.truckId).first()
        if truck and truck.lastKnownLocation:
            request.origin = truck.lastKnownLocation
    
    if not request.origin:
        raise HTTPException(status_code=400, detail="Origin must be provided or truck must have GPS location")
    
    # Add to background tasks
    task_id = f"scrape_{datetime.utcnow().timestamp()}"
    background_tasks.add_task(run_scraper_task, request, db, task_id)
    
    logger.info(f"📍 Scraping initiated: {request.origin} → {request.destination}")
    
    return ScrapeResponse(
        status="pending",
        freightsCount=0,
        message="Scraper started in background",
        taskId=task_id
    )

@router.delete("/{freight_id}")
async def delete_freight(freight_id: int, db: Session = Depends(get_db)):
    freight = db.query(OffersNormalized).filter(OffersNormalized.id == freight_id).first()
    if not freight:
        raise HTTPException(status_code=404, detail="Freight not found")
    db.delete(freight)
    db.commit()
    return {"status": "deleted", "freight_id": freight_id}
