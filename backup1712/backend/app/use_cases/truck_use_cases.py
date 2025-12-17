"""Business logic layer for Truck operations."""

from typing import Optional, List
from datetime import datetime
from ..repositories import TruckRepository
from ..models import Truck
from ..schemas import TruckUpdate


class TruckUseCase:
    """Use case layer for Truck business logic."""
    
    def __init__(self, repository: TruckRepository):
        """Initialize use case with repository.
        
        Args:
            repository: TruckRepository instance
        """
        self.repository = repository
    
    # ========== ACTIVATION OPERATIONS ==========
    def activate_truck(self, truck_id: int) -> Truck:
        """Activate a truck (mark as available).
        
        Args:
            truck_id: ID of truck to activate
        
        Returns:
            Updated Truck object
        
        Raises:
            ValueError: If truck not found
        """
        truck = self.repository.get_by_id(truck_id)
        if not truck:
            raise ValueError(f"Truck {truck_id} not found")
        
        if truck.is_active:
            raise ValueError(f"Truck {truck_id} is already active")
        
        return self.repository.update(truck_id, {"is_active": True})
    
    def deactivate_truck(self, truck_id: int) -> Truck:
        """Deactivate a truck (mark as unavailable).
        
        Args:
            truck_id: ID of truck to deactivate
        
        Returns:
            Updated Truck object
        
        Raises:
            ValueError: If truck not found
        """
        truck = self.repository.get_by_id(truck_id)
        if not truck:
            raise ValueError(f"Truck {truck_id} not found")
        
        return self.repository.deactivate(truck_id)
    
    # ========== GPS OPERATIONS ==========
    def update_truck_location(self, truck_id: int, 
                             lat: float, lng: float, 
                             location: str) -> Truck:
        """Update GPS location for truck.
        
        Args:
            truck_id: ID of truck
            lat: Latitude coordinate
            lng: Longitude coordinate
            location: Formatted location string (e.g., "SK, 82106")
        
        Returns:
            Updated Truck object with GPS info
        
        Raises:
            ValueError: If truck not found or invalid coordinates
        """
        if not (-90 <= lat <= 90):
            raise ValueError(f"Invalid latitude: {lat}")
        if not (-180 <= lng <= 180):
            raise ValueError(f"Invalid longitude: {lng}")
        
        truck = self.repository.get_by_id(truck_id)
        if not truck:
            raise ValueError(f"Truck {truck_id} not found")
        
        return self.repository.update_gps(truck_id, lat, lng, location)
    
    def get_truck_location(self, truck_id: int) -> Optional[dict]:
        """Get current location of truck.
        
        Args:
            truck_id: ID of truck
        
        Returns:
            Dict with lat, lng, location and timestamp, or None if not available
        
        Raises:
            ValueError: If truck not found
        """
        truck = self.repository.get_by_id(truck_id)
        if not truck:
            raise ValueError(f"Truck {truck_id} not found")
        
        if truck.last_known_lat is None or truck.last_known_lng is None:
            return None
        
        return {
            "lat": truck.last_known_lat,
            "lng": truck.last_known_lng,
            "location": truck.last_known_location,
            "updated_at": truck.gps_updated_at
        }
    
    # ========== TRACKING OPERATIONS ==========
    def enable_gps_tracking(self, truck_id: int, gps_vehicle_code: str) -> Truck:
        """Enable GPS tracking for truck with vehicle code.
        
        Args:
            truck_id: ID of truck
            gps_vehicle_code: GPS device code/ID from provider
        
        Returns:
            Updated Truck object with GPS enabled
        
        Raises:
            ValueError: If truck not found
        """
        truck = self.repository.get_by_id(truck_id)
        if not truck:
            raise ValueError(f"Truck {truck_id} not found")
        
        if truck.gps_vehicle_code == gps_vehicle_code:
            raise ValueError(f"GPS code {gps_vehicle_code} already assigned to this truck")
        
        return self.repository.update(truck_id, {
            "gps_vehicle_code": gps_vehicle_code
        })
    
    def disable_gps_tracking(self, truck_id: int) -> Truck:
        """Disable GPS tracking for truck.
        
        Args:
            truck_id: ID of truck
        
        Returns:
            Updated Truck object
        
        Raises:
            ValueError: If truck not found
        """
        truck = self.repository.get_by_id(truck_id)
        if not truck:
            raise ValueError(f"Truck {truck_id} not found")
        
        return self.repository.update(truck_id, {
            "gps_vehicle_code": None
        })
    
    # ========== SEARCH & FILTER ==========
    def search_trucks_by_license_plate(self, license_plate: str) -> Optional[Truck]:
        """Search truck by license plate.
        
        Args:
            license_plate: License plate number
        
        Returns:
            Truck object if found, None otherwise
        """
        return self.repository.get_by_license_plate(license_plate)
    
    def list_available_trucks(self, skip: int = 0, limit: int = 50) -> List[Truck]:
        """Get list of active (available) trucks.
        
        Args:
            skip: Pagination offset
            limit: Pagination limit
        
        Returns:
            List of active Truck objects
        """
        return self.repository.list_active(skip=skip, limit=limit)
    
    def list_tracked_trucks(self, skip: int = 0, limit: int = 50) -> List[Truck]:
        """Get list of trucks with active GPS tracking.
        
        Args:
            skip: Pagination offset
            limit: Pagination limit
        
        Returns:
            List of Truck objects with GPS enabled
        """
        return self.repository.list_with_gps(skip=skip, limit=limit)
    
    def count_active_trucks(self) -> int:
        """Get count of active trucks.
        
        Returns:
            Number of active trucks
        """
        return self.repository.count_active()
    
    # ========== UPDATE OPERATIONS ==========
    def update_truck(self, truck_id: int, 
                    update_data: TruckUpdate) -> Truck:
        """Update truck with validation.
        
        Args:
            truck_id: ID of truck to update
            update_data: TruckUpdate schema with new values
        
        Returns:
            Updated Truck object
        
        Raises:
            ValueError: If truck not found
        """
        truck = self.repository.get_by_id(truck_id)
        if not truck:
            raise ValueError(f"Truck {truck_id} not found")
        
        # Only update fields that were explicitly set
        data = update_data.model_dump(exclude_unset=True)
        return self.repository.update(truck_id, data)
    
    # ========== DELETE OPERATIONS ==========
    def delete_truck(self, truck_id: int) -> bool:
        """Permanently delete truck.
        
        Args:
            truck_id: ID of truck to delete
        
        Returns:
            True if deleted, False if not found
        """
        return self.repository.delete(truck_id)
