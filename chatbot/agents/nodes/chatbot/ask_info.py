from langchain_core.messages import AIMessage
from chatbot.agents.states.state import AgentState
from chatbot.knowledge.field_requirement import FIELD_NAMES_VN
import logging

# --- Cấu hình logging ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def ask_missing_info(state: AgentState):
    logger.info("---NODE: ASK MISSING INFO---")

    missing_fields = state.get("missing_fields", [])
    topic = state.get("topic", "")

    # 1. Chuyển tên trường kỹ thuật sang tiếng Việt
    missing_vn = [FIELD_NAMES_VN.get(f, f) for f in missing_fields]
    missing_str = ", ".join(missing_vn)

    # 2. Tạo câu hỏi dựa trên ngữ cảnh
    msg = ""

    if topic == "meal_suggestion":
        # Với gợi ý món, ưu tiên hỏi Calo hoặc Số đo
        msg = (
            f"🥗 Để thiết kế thực đơn chuẩn cho bạn, mình cần bổ sung: **{missing_str}**.\n\n"
            "📌 Bạn có thể cung cấp theo 1 trong 2 cách:\n"
            "1) **Thông tin cơ thể** → *mình sẽ tự tính dinh dưỡng cho bạn*:\n"
            "   - ⚖️ Cân nặng (kg)\n"
            "   - 📏 Chiều cao (cm hoặc m)\n"
            "   - 🎂 Tuổi\n"
            "   - 🚹 Giới tính (Nam/Nữ)\n"
            "   - 🏃 Mức độ vận động (Ít / Trung bình / Nhiều)\n\n"
            "2) **Mục tiêu dinh dưỡng cụ thể** → *nếu bạn đã biết trước*:\n"
            "   - 🔥 Kcal\n"
            "   - 💪 Protein (g)\n"
            "   - 🍳 Lipid/Fat (g)\n"
            "   - 🍚 Carbohydrate (g)\n\n"
            "💡 *Bạn có thể nhập nhanh ví dụ:*\n"
            "• \"Mình 60kg, cao 170cm, 22 tuổi, nam, vận động nhẹ\"\n"
            "• \"1500 kcal — Protein 100g, Fat 50g, Carb 140g\""
        )

    else:
        # Fallback chung
        msg = f"Mình cần thêm thông tin về **{missing_str}** để xử lý yêu cầu này."

    return {"messages": [AIMessage(content=msg)]}