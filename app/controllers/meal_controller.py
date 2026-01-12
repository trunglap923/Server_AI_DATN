from fastapi import APIRouter, HTTPException
from app.core.container import container
from app.schema.dtos import MealSuggestionRequest
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/meal-plan", tags=["Meal Plan"])

@router.post("/")
async def suggest_meals(request: MealSuggestionRequest):
    try:
        inputs = {
            "user_id": request.user_id,
            "question": request.question,
            "meals_to_generate": request.meals_to_generate,
            "user_profile": request.user_profile
        }
        
        logger.info(f"Received meal suggestion request for user {request.user_id}")
        
        result = await container.meal_workflow_service.run(inputs)
        
        response = {
            "final_menu": result.get("final_menu", []),
            "reason": result.get("reason", ""),
        }

        if not response.get("final_menu"):
            return {"status": "failed", "response": response}

        return {"status": "success", "response": response}

    except Exception as e:
        logger.error(f"Error in suggest_meals: {e}")
        raise HTTPException(status_code=500, detail=str(e))
