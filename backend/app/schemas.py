from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class TruckBase(BaseModel):
    truckType: str = Field(..., description="Truck type, e.g. Volvo FH16")
    cargoLength: float
    cargoWidth: float
    cargoHeight: float
    licensePlate: str = Field(..., description="License plate unique identifier")
    driverName: str
    gpsVehicleCode: str = Field(..., description="GPS Dozor vehicle code")
    isActive: bool = True

class TruckCreate(TruckBase):
    pass

class TruckUpdate(BaseModel):
    truckType: Optional[str] = None
    licensePlate: Optional[str] = None
    driverName: Optional[str] = None
    isActive: Optional[bool] = None

class TruckResponse(TruckBase):
    id: int
    lastKnownLat: Optional[float] = None
    lastKnownLng: Optional[float] = None
    lastKnownLocation: Optional[str] = None
    gpsUpdatedAt: Optional[datetime] = None
    createdAt: datetime
    updatedAt: datetime

    class Config:
        from_attributes = True

class FreightBase(BaseModel):
    loadingPlace: str
    unloadingPlace: str
    dateLoading: str
    weight: Optional[float] = None
    bodyType: Optional[str] = None
    price: Optional[float] = None

class FreightResponse(FreightBase):
    id: int
    externalId: str
    loadingLat: Optional[float] = None
    loadingLon: Optional[float] = None
    currency: str
    createdAt: datetime

    class Config:
        from_attributes = True

class ScrapeRequest(BaseModel):
    origin: Optional[str] = None  # "SK, 93101" or leave empty for GPS
    destination: str = Field(..., description="Destination city/postal code")
    loadingDateFrom: Optional[str] = None  # YYYY-MM-DD
    loadingDateTo: Optional[str] = None
    unloadingDateFrom: Optional[str] = None
    unloadingDateTo: Optional[str] = None
    headless: bool = True
    truckId: Optional[int] = None  # For using truck's GPS location

class ScrapeResponse(BaseModel):
    status: str  # "pending", "completed", "failed"
    freightsCount: int
    message: str
    taskId: Optional[str] = None

