from fastapi import APIRouter, HTTPException
from app.core.container import container
from app.schema.dtos import FoodReplaceRequest
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/food-replace", tags=["Food Replace"])

@router.post("/")
async def replace_food(request: FoodReplaceRequest):
    try:
        logger.info(f"Received food replace request for user {request.user_id}")
        
        food_data = request.food_old.copy()
        bounds = food_data.get("solver_bounds")
        if bounds and isinstance(bounds, list):
             food_data["solver_bounds"] = tuple(bounds)
        elif not bounds:
             food_data["solver_bounds"] = (0.5, 2.0)
             
        inputs = {
            "user_id": request.user_id,
            "food_old": food_data,
        }
        
        result = await container.food_similarity_service.run(inputs)
        
        response = result.get("best_replacement")
        if not response:
             return {"status": "failed", "response": []}
             
        return {"status": "success", "response": {"best_replacement": response}}
        
    except Exception as e:
        logger.error(f"Error in replace_food: {e}")
        raise HTTPException(status_code=500, detail=str(e))
