from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models import Truck
from app.schemas import TruckCreate, TruckUpdate, TruckResponse
from app.services.gps_service import GPSService
import logging

router = APIRouter(prefix="/api/trucks", tags=["trucks"])
logger = logging.getLogger(__name__)

@router.get("", response_model=List[TruckResponse])
async def list_trucks(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    trucks = db.query(Truck).offset(skip).limit(limit).all()
    return trucks

@router.get("/{truck_id}", response_model=TruckResponse)
async def get_truck(truck_id: int, db: Session = Depends(get_db)):
    truck = db.query(Truck).filter(Truck.id == truck_id).first()
    if not truck:
        raise HTTPException(status_code=404, detail="Truck not found")
    return truck

@router.post("", response_model=TruckResponse)
async def create_truck(truck: TruckCreate, db: Session = Depends(get_db)):
    db_truck = Truck(**truck.dict())
    db.add(db_truck)
    db.commit()
    db.refresh(db_truck)
    logger.info(f"✅ Created truck: {db_truck.licensePlate}")
    return db_truck

@router.patch("/{truck_id}", response_model=TruckResponse)
async def update_truck(truck_id: int, truck: TruckUpdate, db: Session = Depends(get_db)):
    db_truck = db.query(Truck).filter(Truck.id == truck_id).first()
    if not db_truck:
        raise HTTPException(status_code=404, detail="Truck not found")
    
    update_data = truck.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_truck, field, value)
    
    db.commit()
    db.refresh(db_truck)
    return db_truck

@router.delete("/{truck_id}")
async def delete_truck(truck_id: int, db: Session = Depends(get_db)):
    truck = db.query(Truck).filter(Truck.id == truck_id).first()
    if not truck:
        raise HTTPException(status_code=404, detail="Truck not found")
    db.delete(truck)
    db.commit()
    return {"status": "deleted", "truck_id": truck_id}

@router.post("/{truck_id}/update-gps")
async def update_gps(truck_id: int, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    truck = db.query(Truck).filter(Truck.id == truck_id).first()
    if not truck:
        raise HTTPException(status_code=404, detail="Truck not found")
    
    gps_service = GPSService()
    background_tasks.add_task(gps_service.update_truck_location, truck, db)
    
    return {"status": "updating", "truck_id": truck_id, "message": "GPS update initiated"}

