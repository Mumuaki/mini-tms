"""
EXAMPLE: Refactoring main.py endpoints to use Repository + UseCase pattern

This file shows the BEFORE and AFTER patterns for common endpoints.
You can apply these patterns to your existing main.py file.

Key principles:
1. Endpoints become thin HTTP handlers
2. Business logic moves to use cases
3. Data access moves to repositories
4. Dependency injection handles layer separation
"""

# ============================================================================
# PATTERN 1: Simple Read (GET single resource)
# ============================================================================

# BEFORE (old monolithic pattern):
"""
@app.get("/freights/{freight_id}", response_model=schemas.FreightResponse)
def get_freight(freight_id: int, db: Session = Depends(database.get_db)):
    freight = db.query(models.Freight).filter(
        models.Freight.id == freight_id
    ).first()
    if not freight:
        raise HTTPException(status_code=404, detail="Freight not found")
    return freight
"""

# AFTER (new clean architecture):
from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from . import database, schemas, models
from .repositories import FreightRepository, TruckRepository
from .use_cases import FreightUseCase, TruckUseCase


# Dependency injection functions
def get_freight_repository(db: Session = Depends(database.get_db)) -> FreightRepository:
    """Inject FreightRepository with database session."""
    return FreightRepository(db)


def get_freight_use_case(
    repo: FreightRepository = Depends(get_freight_repository)
) -> FreightUseCase:
    """Inject FreightUseCase with repository."""
    return FreightUseCase(repo)


def get_truck_repository(db: Session = Depends(database.get_db)) -> TruckRepository:
    """Inject TruckRepository with database session."""
    return TruckRepository(db)


def get_truck_use_case(
    repo: TruckRepository = Depends(get_truck_repository)
) -> TruckUseCase:
    """Inject TruckUseCase with repository."""
    return TruckUseCase(repo)


# Refactored endpoint
def get_freight_refactored(
    freight_id: int,
    use_case: FreightUseCase = Depends(get_freight_use_case)
) -> schemas.FreightResponse:
    """Get single freight by ID. Simple and clean."""
    try:
        freight = use_case.repository.get_by_id(freight_id)
        if not freight:
            raise HTTPException(status_code=404, detail="Freight not found")
        return freight
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================================
# PATTERN 2: List with Filtering (GET multiple resources)
# ============================================================================

# BEFORE (monolithic):
"""
@app.get("/freights", response_model=list[schemas.FreightResponse])
def list_freights(
    skip: int = 0,
    limit: int = 100,
    loading_place: Optional[str] = None,
    unloading_place: Optional[str] = None,
    db: Session = Depends(database.get_db)
):
    query = db.query(models.Freight).filter(models.Freight.is_hidden == False)
    if loading_place:
        query = query.filter(models.Freight.loading_place.ilike(f"%{loading_place}%"))
    if unloading_place:
        query = query.filter(models.Freight.unloading_place.ilike(f"%{unloading_place}%"))
    return query.offset(skip).limit(limit).all()
"""

# AFTER (clean architecture):
def list_freights_refactored(
    skip: int = 0,
    limit: int = 100,
    loading_place: str | None = None,
    unloading_place: str | None = None,
    use_case: FreightUseCase = Depends(get_freight_use_case)
) -> list[schemas.FreightResponse]:
    """List active freights with optional location filters."""
    if loading_place or unloading_place:
        freights = use_case.search_by_location(loading_place, unloading_place)
        return freights[skip : skip + limit]
    
    return use_case.repository.list_active(skip=skip, limit=limit)


# ============================================================================
# PATTERN 3: Update (PATCH resource)
# ============================================================================

# BEFORE (monolithic):
"""
@app.patch("/freights/{freight_id}", response_model=schemas.FreightResponse)
def update_freight(
    freight_id: int,
    freight_update: schemas.FreightUpdate,
    db: Session = Depends(database.get_db)
):
    freight = db.query(models.Freight).filter(
        models.Freight.id == freight_id
    ).first()
    if not freight:
        raise HTTPException(status_code=404, detail="Freight not found")
    
    update_data = freight_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(freight, key, value)
    
    db.commit()
    db.refresh(freight)
    return freight
"""

# AFTER (clean architecture):
def update_freight_refactored(
    freight_id: int,
    freight_update: schemas.FreightUpdate,
    use_case: FreightUseCase = Depends(get_freight_use_case)
) -> schemas.FreightResponse:
    """Update freight - all business logic in use case."""
    try:
        return use_case.update_freight(freight_id, freight_update)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ============================================================================
# PATTERN 4: Delete (DELETE resource)
# ============================================================================

# BEFORE (monolithic):
"""
@app.delete("/freights/{freight_id}")
def delete_freight(
    freight_id: int,
    db: Session = Depends(database.get_db)
):
    freight = db.query(models.Freight).filter(
        models.Freight.id == freight_id
    ).first()
    if not freight:
        raise HTTPException(status_code=404, detail="Freight not found")
    
    db.delete(freight)
    db.commit()
    return {"message": "Deleted"}
"""

# AFTER (clean architecture):
def delete_freight_refactored(
    freight_id: int,
    use_case: FreightUseCase = Depends(get_freight_use_case)
) -> dict:
    """Delete freight - delegates to use case."""
    deleted = use_case.delete_freight(freight_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Freight not found")
    return {"message": "Freight deleted successfully"}


# ============================================================================
# PATTERN 5: Business Logic Operations (Mark as Deal, Hide, etc)
# ============================================================================

# NEW with Use Cases - no old pattern to compare

def mark_freight_as_deal_refactored(
    freight_id: int,
    use_case: FreightUseCase = Depends(get_freight_use_case)
) -> schemas.FreightResponse:
    """Mark freight as deal - pure business logic."""
    try:
        return use_case.mark_as_deal(freight_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


def hide_freight_refactored(
    freight_id: int,
    use_case: FreightUseCase = Depends(get_freight_use_case)
) -> schemas.FreightResponse:
    """Hide freight from search results."""
    try:
        return use_case.hide_freight(freight_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ============================================================================
# PATTERN 6: Truck Endpoints with GPS
# ============================================================================

def get_truck_location_refactored(
    truck_id: int,
    use_case: TruckUseCase = Depends(get_truck_use_case)
) -> dict:
    """Get truck GPS location."""
    try:
        location = use_case.get_truck_location(truck_id)
        if not location:
            raise HTTPException(
                status_code=404,
                detail="Truck not found or GPS location unavailable"
            )
        return location
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


def update_truck_location_refactored(
    truck_id: int,
    lat: float,
    lng: float,
    location: str,
    use_case: TruckUseCase = Depends(get_truck_use_case)
) -> schemas.TruckResponse:
    """Update truck GPS location."""
    try:
        return use_case.update_truck_location(truck_id, lat, lng, location)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================================
# HOW TO APPLY THIS TO YOUR main.py
# ============================================================================

"""
1. Add the dependency injection functions at the top of your main.py:
   - get_freight_repository()
   - get_freight_use_case()
   - get_truck_repository()
   - get_truck_use_case()

2. For each existing endpoint, follow the patterns above:
   - Add use_case parameter with Depends()
   - Replace db.query() calls with use_case.repository methods
   - Move business logic from endpoint to use case methods
   - Update error handling to raise HTTPException

3. Example of updating one endpoint:

   ORIGINAL in main.py:
   @app.get("/freights/{freight_id}")
   def get_freight(freight_id: int, db: Session = Depends(database.get_db)):
       freight = db.query(models.Freight).filter(...).first()
       ...

   UPDATE TO:
   @app.get("/freights/{freight_id}")
   def get_freight(
       freight_id: int,
       use_case: FreightUseCase = Depends(get_freight_use_case)
   ):
       try:
           freight = use_case.repository.get_by_id(freight_id)
           if not freight:
               raise HTTPException(status_code=404, detail="Not found")
           return freight
       except ValueError as e:
           raise HTTPException(status_code=400, detail=str(e))

4. Test each refactored endpoint before deploying.

5. Import statements needed at top of main.py:
   from .repositories import FreightRepository, TruckRepository
   from .use_cases import FreightUseCase, TruckUseCase
"""
