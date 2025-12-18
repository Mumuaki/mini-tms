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
    loading_date = Column(DateTime(timezone=True))
    unloading_date = Column(DateTime(timezone=True), nullable=True)
    cargo_info = Column(String) # Вес, тип кузова и т.д.
    price_original = Column(Float, nullable=True) # Цена от заказчика если есть
    currency = Column(String, default="EUR")
    
    # Рассчитанные данные
    distance_km = Column(Float, nullable=True)
    cost_price = Column(Float, nullable=True) # Себестоимость
    
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

class Truck(Base):
    __tablename__ = "trucks"

    id = Column(Integer, primary_key=True, index=True)
    
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

