<<<<<<< HEAD
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
=======
from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class FreightBase(BaseModel):
    trans_id: str
    loading_place: Optional[str] = None
    unloading_place: Optional[str] = None
    loading_date: Optional[str] = None  # Changed to str
    unloading_date: Optional[str] = None # Changed to str
    cargo_info: Optional[str] = None
    price_original: Optional[float] = None
    currency: str = "EUR"
    
    # New detailed fields
    body_type: Optional[str] = None
    capacity: Optional[str] = None
    ldm: Optional[str] = None
    payment_terms: Optional[str] = None
    additional_description: Optional[str] = None
    distance_origin_to_loading: Optional[float] = None


class FreightCreate(FreightBase):
    pass


class FreightUpdate(BaseModel):
    is_hidden: Optional[bool] = None
    is_deal: Optional[bool] = None
    rate_min: Optional[float] = None
    rate_avg: Optional[float] = None
    rate_max: Optional[float] = None


class FreightResponse(FreightBase):
    id: int
    distance_km: Optional[float] = None
    cost_price: Optional[float] = None
    rate_min: Optional[float] = None
    rate_avg: Optional[float] = None
    rate_max: Optional[float] = None
    is_hidden: bool
    is_deal: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ScrapeRequest(BaseModel):
    origin: Optional[str] = None
    destination: Optional[str] = None
    loading_date_from: Optional[str] = None
    loading_date_to: Optional[str] = None
    unloading_date_from: Optional[str] = None
    unloading_date_to: Optional[str] = None
    headless: bool = True


class ScrapeResponse(BaseModel):
    success: bool
    message: str
    freights_count: int
    new_freights: int

class TruckBase(BaseModel):
    truck_type: str = "Тентованный фургон"
    cargo_length: Optional[float] = None
    cargo_width: Optional[float] = None
    cargo_height: Optional[float] = None
    license_plate: Optional[str] = None
    driver_name: Optional[str] = None
    gps_vehicle_code: Optional[str] = None
>>>>>>> 97953c3 (Initial commit from Specify template)

class TruckCreate(TruckBase):
    pass

class TruckUpdate(BaseModel):
<<<<<<< HEAD
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
=======
    truck_type: Optional[str] = None
    cargo_length: Optional[float] = None
    cargo_width: Optional[float] = None
    cargo_height: Optional[float] = None
    license_plate: Optional[str] = None
    driver_name: Optional[str] = None
    gps_vehicle_code: Optional[str] = None
    is_active: Optional[bool] = None

class TruckResponse(TruckBase):
    id: int
    last_known_lat: Optional[float] = None
    last_known_lng: Optional[float] = None
    last_known_location: Optional[str] = None
    gps_updated_at: Optional[datetime] = None
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
>>>>>>> 97953c3 (Initial commit from Specify template)

    class Config:
        from_attributes = True

<<<<<<< HEAD
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
    loadingDateFrom: Optional[str] = None  # DD-MM-YYYY
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

=======
>>>>>>> 97953c3 (Initial commit from Specify template)
