from fastapi import APIRouter, HTTPException, Depends
from app.schema.food_payload import FoodItemPayload
from app.services.features.food_management_service import FoodManagementService
from app.core.container import container
import logging

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/manage-food",
    tags=["Food Management (CRUD)"]
)

def get_service():
    return container.food_management_service

@router.post("/save")
def save_food(item: FoodItemPayload, service: FoodManagementService = Depends(get_service)):
    try:
        service.save_food(item)
        return {"status": "success"}
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.error(f"Error saving food: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/delete/{meal_id}")
def delete_food(meal_id: str, service: FoodManagementService = Depends(get_service)):
    try:
        service.delete_food(meal_id)
        return {"status": "success"}
    except Exception as e:
        logger.error(f"Error deleting food: {e}")
        raise HTTPException(status_code=500, detail=str(e))
