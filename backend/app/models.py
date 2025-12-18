<<<<<<< HEAD
from sqlalchemy import Column, Integer, String, Float, DateTime, JSON, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base
=======
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text
from sqlalchemy.sql import func
from .database import Base

class Freight(Base):
    __tablename__ = "freights"

    id = Column(Integer, primary_key=True, index=True)
    trans_id = Column(String, unique=True, index=True)  # ID предложения в Trans.eu
    
    # Данные из Trans.eu
    loading_place = Column(String)
    unloading_place = Column(String)
    loading_date = Column(String) # Store raw string to support ranges (10-12.12)
    unloading_date = Column(String, nullable=True)
    cargo_info = Column(String) # Вес, тип кузова и т.д.
    price_original = Column(Float, nullable=True) # Цена от заказчика если есть
    currency = Column(String, default="EUR")
    
    # Рассчитанные данные
    distance_km = Column(Float, nullable=True)
    cost_price = Column(Float, nullable=True) # Себестоимость
    
    # Detailed fields from modal
    body_type = Column(String, nullable=True) # Тип кузова
    capacity = Column(String, nullable=True) # Грузоподъемность/Тоннаж
    ldm = Column(String, nullable=True) # Loading meters
    payment_terms = Column(String, nullable=True) # Условия оплаты (200 EUR 55 days)
    additional_description = Column(String, nullable=True) # Доп описание
    
    # Расчетные расстояния
    distance_origin_to_loading = Column(Float, nullable=True) # От нас до загрузки
    
    # Ставки
    rate_min = Column(Float, nullable=True)
    rate_avg = Column(Float, nullable=True)
    rate_max = Column(Float, nullable=True)
    
    # Статусы
    is_hidden = Column(Boolean, default=False) # Черный список/скрыто
    is_deal = Column(Boolean, default=False) # Перешло в сделку
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class Settings(Base):
    __tablename__ = "settings"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String, unique=True, index=True)
    value = Column(String)
    description = Column(String, nullable=True)

class Deal(Base):
    __tablename__ = "deals"

    id = Column(Integer, primary_key=True, index=True)
    freight_id = Column(Integer, nullable=True) # Ссылка на груз, если создан из него
    
    client_name = Column(String)
    contact_person = Column(String, nullable=True)
    final_rate = Column(Float)
    currency = Column(String, default="EUR")
    
    status = Column(String, default="new") # new, in_progress, completed, paid
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
>>>>>>> 97953c3 (Initial commit from Specify template)

class Truck(Base):
    __tablename__ = "trucks"

    id = Column(Integer, primary_key=True, index=True)
<<<<<<< HEAD
    truckType = Column(String, nullable=False)  # "Volvo FH16"
    cargoLength = Column(Float, nullable=False)
    cargoWidth = Column(Float, nullable=False)
    cargoHeight = Column(Float, nullable=False)
    licensePlate = Column(String, unique=True, nullable=False)
    driverName = Column(String, nullable=False)
    gpsVehicleCode = Column(String, nullable=False)  # GPS Dozor identifier
    lastKnownLat = Column(Float, nullable=True)
    lastKnownLng = Column(Float, nullable=True)
    lastKnownLocation = Column(String, nullable=True)  # "SK, 93101"
    gpsUpdatedAt = Column(DateTime, nullable=True)
    isActive = Column(Boolean, default=True)
    createdAt = Column(DateTime, default=datetime.utcnow)
    updatedAt = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    gpsLocations = relationship("VehicleLocation", back_populates="truck")

class VehicleLocation(Base):
    __tablename__ = "vehicle_locations"

    id = Column(Integer, primary_key=True, index=True)
    truckId = Column(Integer, ForeignKey("trucks.id"), nullable=False)
    lat = Column(Float, nullable=False)
    lon = Column(Float, nullable=False)
    placeName = Column(String, nullable=True)
    country = Column(String, nullable=True)
    accuracy = Column(Float, nullable=True)
    measuredAt = Column(DateTime, nullable=False)
    updatedAt = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    truck = relationship("Truck", back_populates="gpsLocations")

class OffersNormalized(Base):
    __tablename__ = "offers_normalized"

    id = Column(Integer, primary_key=True, index=True)
    externalId = Column(String, unique=True, nullable=False)  # Trans.eu ID
    loadingPlace = Column(String, nullable=False)
    unloadingPlace = Column(String, nullable=False)
    loadingLat = Column(Float, nullable=True)
    loadingLon = Column(Float, nullable=True)
    unloadingLat = Column(Float, nullable=True)
    unloadingLon = Column(Float, nullable=True)
    dateLoading = Column(String, nullable=False)  # YYYY-MM-DD
    weight = Column(Float, nullable=True)  # tons
    bodyType = Column(String, nullable=True)  # FTL, LTL, etc.
    price = Column(Float, nullable=True)  # EUR
    currency = Column(String, default="EUR")
    rawJson = Column(JSON, nullable=True)
    createdAt = Column(DateTime, default=datetime.utcnow)
    scrapedAt = Column(DateTime, default=datetime.utcnow)
=======
    
    # Truck details
    truck_type = Column(String, default="Тентованный фургон")  # e.g. "Тентованный фургон"
    cargo_length = Column(Float, nullable=True)  # meters
    cargo_width = Column(Float, nullable=True)   # meters
    cargo_height = Column(Float, nullable=True)  # meters
    license_plate = Column(String, nullable=True)
    driver_name = Column(String, nullable=True)
    
    # GPS tracking
    gps_vehicle_code = Column(String, nullable=True)  # Code from GPS Dozor API
    last_known_lat = Column(Float, nullable=True)
    last_known_lng = Column(Float, nullable=True)
    last_known_location = Column(String, nullable=True)  # Formatted address (e.g. "SK, 82106")
    gps_updated_at = Column(DateTime(timezone=True), nullable=True)
    
    # Status
    is_active = Column(Boolean, default=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
>>>>>>> 97953c3 (Initial commit from Specify template)

