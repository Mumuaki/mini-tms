from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class FreightBase(BaseModel):
    trans_id: str
    loading_place: Optional[str] = None
    unloading_place: Optional[str] = None
    loading_date: Optional[datetime] = None
    unloading_date: Optional[datetime] = None
    cargo_info: Optional[str] = None
    price_original: Optional[float] = None
    currency: str = "EUR"


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

class TruckCreate(TruckBase):
    pass

class TruckUpdate(BaseModel):
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

    class Config:
        from_attributes = True

