from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

# Correct relative imports for modules three levels up
from ... import schemas, models # schemas is used by roadmap_schemas
from ...database import get_db_session
from ... import security

# Specific roadmap imports
from ..schemas import roadmap_schemas
from ..services import roadmap_service

router = APIRouter(
    prefix="/roadmap",
    tags=["Roadmap"]
)

# Note: Since roadmap_service uses synchronous file I/O with a threading.Lock,
# these endpoints are kept async but will block the event loop during file access.
# For high concurrency, refactor roadmap_service to use async file I/O.

@router.get("/items", response_model=List[roadmap_schemas.RoadmapItem])
async def get_roadmap_items():
    """Retrieves all roadmap items."""
    items = roadmap_service.get_roadmap_items()
    if items is None: # Service might return None if file not found or empty
        return []
    return items

@router.post(
    "/item", 
    response_model=roadmap_schemas.RoadmapItem, 
    status_code=status.HTTP_201_CREATED
)
async def add_roadmap_item(
    item_data: roadmap_schemas.RoadmapItemCreate,
    # current_user: models.User = Depends(security.require_admin) # Assuming admin for now
):
    """Adds a new roadmap item."""
    # Ensure current_user is utilized if uncommented, or remove if not needed yet.
    # For now, let's assume public or service handles auth.
    try:
        new_item = roadmap_service.add_roadmap_item(item_data.model_dump()) # Pass data as dict
        return new_item
    except Exception as e: # Catch potential exceptions from the service
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.delete("/item/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_roadmap_item(
    item_id: int,
    # current_user: models.User = Depends(security.require_admin) # Assuming admin
):
    """Deletes a roadmap item."""
    try:
        success = roadmap_service.delete_roadmap_item(item_id)
        if not success:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Roadmap item not found")
        return  # Return None for 204 No Content
    except ValueError as e: # Catch specific errors like item not found from service
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.put("/item/{item_id}/status", response_model=roadmap_schemas.RoadmapItem)
async def update_roadmap_item_status(
    item_id: int,
    status_update: roadmap_schemas.RoadmapItemUpdateStatus,
    # current_user: models.User = Depends(security.require_admin) # Assuming admin
):
    """Updates the status of a roadmap item."""
    try:
        updated_item = roadmap_service.update_roadmap_item_status(item_id, status_update.status)
        if updated_item is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Roadmap item not found or status unchanged")
        return updated_item
    except ValueError as e: # Catch specific errors
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)) 