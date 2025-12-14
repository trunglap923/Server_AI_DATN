from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from chatbot.agents.graphs.food_similarity_graph import food_similarity_graph
import logging

# --- Cấu hình logging ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Định nghĩa request body ---
class Request(BaseModel):
    user_id: str
    food_old: dict

# --- Tạo router ---
router = APIRouter(
    prefix="/food-replace",
    tags=["Food Replace"]
)

try:
    replace_app = food_similarity_graph()
except Exception as e:
    logger.error(f"❌ Failed to compile Food Graph: {e}")
    raise e

@router.post("/")
def replace_food(request: Request):
    try:
        logger.info(f"Nhận được yêu cầu thay thế món từ user: {request.user_id}")
        
        food_data = request.food_old.copy()
        bounds = food_data.get("solver_bounds")
        
        if bounds and isinstance(bounds, list):
            food_data["solver_bounds"] = tuple(bounds)
        elif not bounds:
            food_data["solver_bounds"] = (0.5, 2.0)

        initial_state = {
            "user_id": request.user_id,
            "food_old": food_data,
        }

        final_state = replace_app.invoke(initial_state)
        response = {"best_replacement": final_state["best_replacement"]}
        
        if not response:
            return {"status": "failed", "response": []}

        return {"status": "success", "response": response}

    except Exception as e:
        logger.error(f"Lỗi xử lý thay thế món: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Lỗi hệ thống: {str(e)}")