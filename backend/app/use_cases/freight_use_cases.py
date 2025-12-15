"""Business logic layer for Freight operations."""

from typing import Optional, List, Dict, Any
from datetime import datetime
from ..repositories import FreightRepository
from ..models import Freight
from ..schemas import FreightUpdate


class FreightUseCase:
    """Use case layer for Freight business logic."""
    
    def __init__(self, repository: FreightRepository):
        """Initialize use case with repository.
        
        Args:
            repository: FreightRepository instance
        """
        self.repository = repository
    
    # ========== MARK OPERATIONS ==========
    def mark_as_deal(self, freight_id: int) -> Freight:
        """Mark freight as a deal / closed.
        
        Args:
            freight_id: ID of freight to mark
        
        Returns:
            Updated Freight object
        
        Raises:
            ValueError: If freight not found or already marked as deal
        """
        freight = self.repository.get_by_id(freight_id)
        if not freight:
            raise ValueError(f"Freight {freight_id} not found")
        
        if freight.is_deal:
            raise ValueError(f"Freight {freight_id} is already marked as a deal")
        
        return self.repository.update(freight_id, {
            "is_deal": True,
            "marked_as_deal_at": datetime.utcnow()
        })
    
    def hide_freight(self, freight_id: int) -> Freight:
        """Hide freight from search results (soft delete).
        
        Args:
            freight_id: ID of freight to hide
        
        Returns:
            Updated Freight object
        
        Raises:
            ValueError: If freight not found
        """
        freight = self.repository.get_by_id(freight_id)
        if not freight:
            raise ValueError(f"Freight {freight_id} not found")
        
        return self.repository.soft_delete(freight_id)
    
    def unhide_freight(self, freight_id: int) -> Freight:
        """Unhide previously hidden freight.
        
        Args:
            freight_id: ID of freight to unhide
        
        Returns:
            Updated Freight object
        
        Raises:
            ValueError: If freight not found
        """
        return self.repository.update(freight_id, {"is_hidden": False})
    
    # ========== SEARCH & FILTER OPERATIONS ==========
    def search_by_location(self, 
                          loading_place: Optional[str] = None,
                          unloading_place: Optional[str] = None) -> List[Freight]:
        """Search freights by loading/unloading locations.
        
        Args:
            loading_place: Loading city/country (partial match)
            unloading_place: Unloading city/country (partial match)
        
        Returns:
            List of matching Freight objects
        """
        return self.repository.search(
            loading_place=loading_place,
            unloading_place=unloading_place,
            exclude_hidden=True
        )
    
    def get_active_deals(self, skip: int = 0, limit: int = 50) -> List[Freight]:
        """Get all freights marked as deals (not hidden).
        
        Args:
            skip: Pagination offset
            limit: Pagination limit
        
        Returns:
            List of Freight objects marked as deals
        """
        return self.repository.list_deals(skip=skip, limit=limit)
    
    def get_freight_by_trans_eu_id(self, trans_eu_id: str) -> Optional[Freight]:
        """Look up freight by Trans.eu listing ID.
        
        Args:
            trans_eu_id: Trans.eu offer ID
        
        Returns:
            Freight object if found, None otherwise
        """
        return self.repository.get_by_trans_id(trans_eu_id)
    
    # ========== UPDATE OPERATIONS ==========
    def update_freight(self, freight_id: int, 
                      update_data: FreightUpdate) -> Freight:
        """Update freight with validation.
        
        Args:
            freight_id: ID of freight to update
            update_data: FreightUpdate schema with new values
        
        Returns:
            Updated Freight object
        
        Raises:
            ValueError: If freight not found
        """
        freight = self.repository.get_by_id(freight_id)
        if not freight:
            raise ValueError(f"Freight {freight_id} not found")
        
        # Only update fields that were explicitly set
        data = update_data.model_dump(exclude_unset=True)
        return self.repository.update(freight_id, data)
    
    def add_rating(self, freight_id: int, rating: int, comment: str = "") -> Freight:
        """Add or update rating for freight.
        
        Args:
            freight_id: ID of freight
            rating: Rating value (1-5)
            comment: Optional comment about the freight
        
        Returns:
            Updated Freight object
        
        Raises:
            ValueError: If freight not found or rating invalid
        """
        if not 1 <= rating <= 5:
            raise ValueError("Rating must be between 1 and 5")
        
        return self.repository.update(freight_id, {
            "rating": rating,
            "rating_comment": comment if comment else None,
            "rated_at": datetime.utcnow()
        })
    
    # ========== ANALYTICS ==========
    def count_active_freight(self) -> int:
        """Get count of active (not hidden) freights.
        
        Returns:
            Number of active freight entries
        """
        return self.repository.count_active()
    
    def get_active_freight_by_origin(self, origin: str) -> List[Freight]:
        """Get all active freights from specific origin.
        
        Args:
            origin: Origin city/country name (partial match)
        
        Returns:
            List of matching Freight objects
        """
        return self.repository.search(loading_place=origin, exclude_hidden=True)
    
    def get_active_freight_by_destination(self, destination: str) -> List[Freight]:
        """Get all active freights to specific destination.
        
        Args:
            destination: Destination city/country name (partial match)
        
        Returns:
            List of matching Freight objects
        """
        return self.repository.search(unloading_place=destination, exclude_hidden=True)
    
    # ========== DELETE OPERATIONS ==========
    def delete_freight(self, freight_id: int) -> bool:
        """Permanently delete freight (hard delete).
        
        Args:
            freight_id: ID of freight to delete
        
        Returns:
            True if deleted, False if not found
        """
        return self.repository.delete(freight_id)
