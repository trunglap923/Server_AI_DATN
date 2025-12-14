from chatbot.agents.states.state import AgentState
from langchain_core.messages import AIMessage, SystemMessage, HumanMessage
from chatbot.models.llm_setup import llm
import logging

# --- Cấu hình logging ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def select_food_plan(state: AgentState):
    logger.info("---SELECT FOOD PLAN---")

    user_profile = state.get("user_profile", {})
    suggested_meals = state.get("suggested_meals", [])
    messages = state.get("messages", [])
    user_message = messages[-1].content if messages else state.get("question", "")
    
    if not suggested_meals:
        return {
            "messages": [AIMessage(content="Xin lỗi, dựa trên tiêu chí của bạn, tôi không tìm thấy món ăn nào phù hợp trong dữ liệu.")]
        }


    suggested_meals_text = "\n".join(
        f"Món {i+1}: {doc.metadata.get('name', 'Không rõ')}\n"
        f"   - Dinh dưỡng: {doc.metadata.get('kcal', '?')} kcal | "
        f"P: {doc.metadata.get('protein', '?')}g | L: {doc.metadata.get('totalfat', '?')}g | C: {doc.metadata.get('carbs', '?')}g\n"
        for i, doc in enumerate(suggested_meals)
    )

    system_prompt = f"""
    Bạn là chuyên gia dinh dưỡng AI.

    HỒ SƠ NGƯỜI DÙNG:
    - Mục tiêu: {user_profile.get('targetcalories', 'N/A')} kcal/ngày
    - Macro (P/F/C): {user_profile.get('protein', '?')}g / {user_profile.get('totalfat', '?')}g / {user_profile.get('carbohydrate', '?')}g
    - Chế độ: {user_profile.get('diet', 'Cân bằng')}

    CÂU HỎI:
    {user_message}

    DANH SÁCH ỨNG VIÊN TỪ DATABASE:
    {suggested_meals_text}

    NHIỆM VỤ:
    1. Dựa vào câu hỏi của người dùng, hãy chọn ra 2-3 món phù hợp nhất từ danh sách trên.
    2. Giải thích lý do chọn (dựa trên sự phù hợp về Calo/Macro hoặc khẩu vị).
    3. TUYỆT ĐỐI KHÔNG bịa ra món không có trong danh sách.
    """
    
    try:
        response = llm.invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_message)
        ])

        print("💬 AI Response:", response.content)
        return {"messages": [response]}

    except Exception as e:
        print(f"⚠️ Lỗi sinh câu trả lời: {e}")
        return {"messages": [AIMessage(content="Xin lỗi, đã có lỗi xảy ra khi xử lý thông tin món ăn.")]}