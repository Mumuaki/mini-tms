from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from ..models import Truck


class TruckRepository:
    """Repository for Truck model - handles all database operations."""
    
    def __init__(self, db: Session):
        """Initialize repository with database session.
        
        Args:
            db: SQLAlchemy session
        """
        self.db = db
    
    # ========== CREATE ==========
    def create(self, truck_data: Dict[str, Any]) -> Truck:
        """Create new truck entry.
        
        Args:
            truck_data: Dictionary with truck attributes
        
        Returns:
            Created Truck object
        """
        truck = Truck(**truck_data)
        self.db.add(truck)
        self.db.commit()
        self.db.refresh(truck)
        return truck
    
    # ========== READ ==========
    def get_by_id(self, truck_id: int) -> Optional[Truck]:
        """Get truck by ID.
        
        Args:
            truck_id: Truck ID
        
        Returns:
            Truck object or None
        """
        return self.db.query(Truck).filter(Truck.id == truck_id).first()
    
    def get_by_license_plate(self, license_plate: str) -> Optional[Truck]:
        """Get truck by license plate.
        
        Args:
            license_plate: License plate number
        
        Returns:
            Truck object or None
        """
        return self.db.query(Truck).filter(Truck.license_plate == license_plate).first()
    
    def list_all(self, skip: int = 0, limit: int = 100) -> List[Truck]:
        """Get all trucks with pagination.
        
        Args:
            skip: Number of records to skip
            limit: Number of records to return
        
        Returns:
            List of Truck objects
        """
        return self.db.query(Truck).offset(skip).limit(limit).all()
    
    def list_active(self, skip: int = 0, limit: int = 100) -> List[Truck]:
        """Get only active trucks.
        
        Args:
            skip: Offset for pagination
            limit: Limit for pagination
        
        Returns:
            List of active Truck objects
        """
        return self.db.query(Truck).filter(
            Truck.is_active == True
        ).offset(skip).limit(limit).all()
    
    def list_with_gps(self, skip: int = 0, limit: int = 100) -> List[Truck]:
        """Get trucks that have GPS tracking enabled.
        
        Args:
            skip: Offset for pagination
            limit: Limit for pagination
        
        Returns:
            List of Truck objects with GPS codes
        """
        return self.db.query(Truck).filter(
            Truck.gps_vehicle_code.isnot(None),
            Truck.is_active == True
        ).offset(skip).limit(limit).all()
    
    def count_active(self) -> int:
        """Count active trucks.
        
        Returns:
            Number of active trucks
        """
        return self.db.query(Truck).filter(Truck.is_active == True).count()
    
    # ========== UPDATE ==========
    def update(self, truck_id: int, data: Dict[str, Any]) -> Truck:
        """Update truck by ID.
        
        Args:
            truck_id: ID of truck to update
            data: Dictionary of fields to update (only non-None values)
        
        Returns:
            Updated Truck object
        
        Raises:
            ValueError: If truck not found
        """
        truck = self.get_by_id(truck_id)
        if not truck:
            raise ValueError(f"Truck with id {truck_id} not found")
        
        # Update only provided fields
        for key, value in data.items():
            if value is not None and hasattr(truck, key):
                setattr(truck, key, value)
        
        self.db.commit()
        self.db.refresh(truck)
        return truck
    
    def update_gps(self, truck_id: int, 
                   lat: float, lng: float, 
                   location: str) -> Truck:
        """Update GPS location for truck.
        
        Args:
            truck_id: ID of truck to update
            lat: Latitude coordinate
            lng: Longitude coordinate
            location: Formatted location string (e.g., "SK, 82106")
        
        Returns:
            Updated Truck object
        
        Raises:
            ValueError: If truck not found
        """
        from datetime import datetime
        
        return self.update(truck_id, {
            'last_known_lat': lat,
            'last_known_lng': lng,
            'last_known_location': location,
            'gps_updated_at': datetime.utcnow()
        })
    
    # ========== DELETE ==========
    def delete(self, truck_id: int) -> bool:
        """Delete truck by ID.
        
        Args:
            truck_id: ID of truck to delete
        
        Returns:
            True if deleted, False if not found
        """
        truck = self.get_by_id(truck_id)
        if not truck:
            return False
        
        self.db.delete(truck)
        self.db.commit()
        return True
    
    def deactivate(self, truck_id: int) -> Truck:
        """Deactivate truck (soft delete).
        
        Args:
            truck_id: ID of truck to deactivate
        
        Returns:
            Updated Truck object
        
        Raises:
            ValueError: If truck not found
        """
        return self.update(truck_id, {"is_active": False})