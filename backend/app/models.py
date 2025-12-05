from sqlalchemy import Column, Integer, String, Float, DateTime, JSON, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base

class Truck(Base):
    __tablename__ = "trucks"

    id = Column(Integer, primary_key=True, index=True)
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

