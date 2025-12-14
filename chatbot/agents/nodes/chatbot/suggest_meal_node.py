from chatbot.agents.states.state import AgentState
from chatbot.agents.tools.daily_meal_suggestion import daily_meal_suggestion
import logging

# --- Cấu hình logging ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def suggest_meal_node(state: AgentState):
    logger.info("---SUGGEST MEAL NODE---")

    user_id = state.get("user_id", 1)
    user_profile = state.get("user_profile", {})
    meals_to_generate = state.get("meals_to_generate", [])
    messages = state.get("messages", [])
    
    if messages:
        question = messages[-1].content
    else:
        question = "Gợi ý thực đơn tiêu chuẩn"
        
    tool_input = {
        "user_id": user_id,
        "user_profile": user_profile,
        "question": question,
        "meals_to_generate": meals_to_generate
    }

    logger.info(f"👉 Gọi Tool: daily_meal_suggestion")

    try:
        result = daily_meal_suggestion.invoke(tool_input)
        return {
            "final_menu": result.get("final_menu"),
            "reason": result.get("reason"),
        }
    except Exception as e:
        print(f"❌ Lỗi khi chạy tool: {e}")
        return {
            "final_menu": [],
            "error": str(e)
        }
