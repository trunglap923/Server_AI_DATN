from langchain_core.messages import AIMessage
from chatbot.agents.states.state import AgentState
import logging

# --- Cấu hình logging ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def generate_final_response(state: AgentState):
    logger.info("---NODE: FINAL RESPONSE---")
    menu = state.get("final_menu", [])
    reason = state.get("reason", "")
    profile = state.get("user_profile", {})
    
    if not menu:
        return {"messages": [AIMessage(content="Xin lỗi, tôi chưa thể tạo thực đơn lúc này.")]}

    meal_priority = {"sáng": 1, "trưa": 2, "tối": 3}
    sorted_menu = sorted(
        menu,
        key=lambda x: meal_priority.get(x.get('assigned_meal', '').lower(), 99)
    )
    
    output_text = "📋 **THỰC ĐƠN DINH DƯỠNG CÁ NHÂN HÓA**\n"
    output_text += f"🎯 Mục tiêu: {int(profile.get('targetcalories', 0))} Kcal | {int(profile.get('protein', 0))}g Protein\n\n"
    
    current_meal = None

    for dish in sorted_menu:
        meal_name = dish.get('assigned_meal', 'Khác').upper()

        if meal_name != current_meal:
            current_meal = meal_name
            output_text += f"🍽️ **BỮA {current_meal}**:\n"

        scale = dish.get('portion_scale', 1.0)
        scale_info = f" (x{scale} suất)" if scale != 1.0 else ""

        output_text += f"   • **{dish['name']}**{scale_info}\n"
        output_text += f"     └─ {dish['final_kcal']} Kcal | {dish['final_protein']}g Đạm | {dish['final_totalfat']}g Béo | {dish['final_carbs']}g Bột\n"

    if reason:
        output_text += f"\n💡 **Góc nhìn chuyên gia:**\n{reason}"

    return {"messages": [AIMessage(content=output_text)]}
    