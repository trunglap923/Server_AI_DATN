from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from chatbot.agents.graphs.meal_suggestion_graph import meal_plan_graph
import logging

# --- Cấu hình logging ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Định nghĩa request body ---
class Request(BaseModel):
    user_id: str
    meals_to_generate: list # VD: ["sáng", "trưa", "tối"]

# --- Tạo router ---
router = APIRouter(
    prefix="/meal-plan",
    tags=["Meal Plan"]
)

try:
    meal_app = meal_plan_graph()
    logger.info("✅ Meal Plan Graph compiled successfully!")
except Exception as e:
    logger.error(f"❌ Failed to compile Meal Plan Graph: {e}")
    raise e

# --- Route xử lý ---
@router.post("/")
def generate_meal_plan(request: Request):
    try:
        logger.info(f"Nhận yêu cầu lên thực đơn cho user: {request.user_id} - Bữa: {request.meals_to_generate}")

        initial_state = {
            "user_id": request.user_id,
            "meals_to_generate": request.meals_to_generate,
        }

        final_state = meal_app.invoke(initial_state)
        response = {
            "final_menu": final_state["final_menu"],
            "reason": final_state["reason"]
        }
        
        if not response["final_menu"]:
            return {"status": "failed", "response": []}

        return {"status": "success", "response": response}

    except Exception as e:
        logger.error(f"Lỗi tạo thực đơn: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Lỗi hệ thống: {str(e)}")