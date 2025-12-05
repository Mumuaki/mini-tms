from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import VehicleLocation
from app.services.gps_service import GPSService

router = APIRouter(prefix="/api/gps", tags=["gps"])

@router.get("/history/{truck_id}")
async def get_gps_history(truck_id: int, limit: int = 100, db: Session = Depends(get_db)):
    locations = db.query(VehicleLocation).filter(
        VehicleLocation.truckId == truck_id
    ).order_by(VehicleLocation.measuredAt.desc()).limit(limit).all()
    
    return locations

@router.post("/geocode")
async def reverse_geocode(lat: float, lon: float):
    gps_service = GPSService()
    result = await gps_service.reverse_geocode_structured(lat, lon)
    return result
