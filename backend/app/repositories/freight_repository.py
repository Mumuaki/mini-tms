from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from ..models import Freight


class FreightRepository:
    """Repository for Freight model - handles all database operations."""
    
    def __init__(self, db: Session):
        """Initialize repository with database session.
        
        Args:
            db: SQLAlchemy session
        """
        self.db = db
    
    # ========== CREATE ==========
    def create(self, freight_data: Dict[str, Any]) -> Freight:
        """Create new freight entry.
        
        Args:
            freight_data: Dictionary with freight attributes
        
        Returns:
            Created Freight object
        
        Raises:
            IntegrityError: If trans_id already exists
        """
        freight = Freight(**freight_data)
        self.db.add(freight)
        self.db.commit()
        self.db.refresh(freight)
        return freight
    
    # ========== READ ==========
    def get_by_id(self, freight_id: int) -> Optional[Freight]:
        """Get freight by ID.
        
        Args:
            freight_id: Freight ID
        
        Returns:
            Freight object or None
        """
        return self.db.query(Freight).filter(Freight.id == freight_id).first()
    
    def get_by_trans_id(self, trans_id: str) -> Optional[Freight]:
        """Get freight by Trans.eu ID.
        
        Args:
            trans_id: Trans.eu freight ID
        
        Returns:
            Freight object or None
        """
        return self.db.query(Freight).filter(Freight.trans_id == trans_id).first()
    
    def list_all(self, skip: int = 0, limit: int = 100) -> List[Freight]:
        """Get all freights with pagination.
        
        Args:
            skip: Number of records to skip
            limit: Number of records to return
        
        Returns:
            List of Freight objects
        """
        return self.db.query(Freight).offset(skip).limit(limit).all()
    
    def list_active(self, skip: int = 0, limit: int = 100) -> List[Freight]:
        """Get only non-hidden freights.
        
        Args:
            skip: Offset for pagination
            limit: Limit for pagination
        
        Returns:
            List of active Freight objects
        """
        return self.db.query(Freight).filter(
            Freight.is_hidden == False
        ).offset(skip).limit(limit).all()
    
    def list_deals(self, skip: int = 0, limit: int = 100) -> List[Freight]:
        """Get freights marked as deals.
        
        Args:
            skip: Offset for pagination
            limit: Limit for pagination
        
        Returns:
            List of Freight objects marked as deals
        """
        return self.db.query(Freight).filter(
            Freight.is_deal == True
        ).offset(skip).limit(limit).all()
    
    def search(self, 
               loading_place: Optional[str] = None,
               unloading_place: Optional[str] = None,
               exclude_hidden: bool = True) -> List[Freight]:
        """Search freights by locations.
        
        Args:
            loading_place: Loading location to filter by
            unloading_place: Unloading location to filter by
            exclude_hidden: Whether to exclude hidden freights
        
        Returns:
            List of matching Freight objects
        """
        query = self.db.query(Freight)
        
        if exclude_hidden:
            query = query.filter(Freight.is_hidden == False)
        
        if loading_place:
            query = query.filter(Freight.loading_place.ilike(f"%{loading_place}%"))
        
        if unloading_place:
            query = query.filter(Freight.unloading_place.ilike(f"%{unloading_place}%"))
        
        return query.all()
    
    def count_active(self) -> int:
        """Count active (non-hidden) freights.
        
        Returns:
            Number of active freights
        """
        return self.db.query(Freight).filter(Freight.is_hidden == False).count()
    
    # ========== UPDATE ==========
    def update(self, freight_id: int, data: Dict[str, Any]) -> Freight:
        """Update freight by ID.
        
        Args:
            freight_id: ID of freight to update
            data: Dictionary of fields to update (only non-None values)
        
        Returns:
            Updated Freight object
        
        Raises:
            ValueError: If freight not found
        """
        freight = self.get_by_id(freight_id)
        if not freight:
            raise ValueError(f"Freight with id {freight_id} not found")
        
        # Update only provided fields
        for key, value in data.items():
            if value is not None and hasattr(freight, key):
                setattr(freight, key, value)
        
        self.db.commit()
        self.db.refresh(freight)
        return freight
    
    # ========== DELETE ==========
    def delete(self, freight_id: int) -> bool:
        """Delete freight by ID.
        
        Args:
            freight_id: ID of freight to delete
        
        Returns:
            True if deleted, False if not found
        """
        freight = self.get_by_id(freight_id)
        if not freight:
            return False
        
        self.db.delete(freight)
        self.db.commit()
        return True
    
    def soft_delete(self, freight_id: int) -> Freight:
        """Mark freight as hidden (soft delete).
        
        Args:
            freight_id: ID of freight to hide
        
        Returns:
            Updated Freight object
        
        Raises:
            ValueError: If freight not found
        """
        return self.update(freight_id, {"is_hidden": True})
