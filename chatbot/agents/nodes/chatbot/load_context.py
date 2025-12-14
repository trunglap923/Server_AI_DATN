
from pydantic import BaseModel, Field
from chatbot.agents.states.state import AgentState
from chatbot.models.llm_setup import llm
from typing import Literal, List, Optional
from langchain_core.messages import SystemMessage
from chatbot.utils.chat_history import get_chat_history
from chatbot.utils.restriction import get_restrictions
from chatbot.utils.user_profile import get_user_by_id
import logging

# --- Cấu hình logging ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DiseaseType = Literal[
    "Khỏe mạnh",
    "Suy thận",
    "Xơ gan, Viêm gan",
    "Gout",
    "Sỏi thận",
    "Suy dinh dưỡng",
    "Bỏng nặng",
    "Thiếu máu thiếu sắt",
    "Bệnh tim mạch",
    "Tiểu đường",
    "Loãng xương",
    "Phụ nữ mang thai",
    "Viêm loét, trào ngược dạ dày",
    "Hội chứng ruột kích thích",
    "Viêm khớp",
    "Tăng huyết áp"
]

class MacroGoals(BaseModel):
    targetcalories: float = Field(..., description="Tổng calo mục tiêu (TDEE +/- goal)")
    protein: float = Field(..., description="Protein (gram)")
    totalfat: float = Field(..., description="Lipid/Fat (gram)")
    carbohydrate: float = Field(..., description="Tinh bột (gram)")
    heathStatus: DiseaseType = Field(..., description="Tình trạng sức khỏe")
    diet: str = Field(..., description="Chế độ ăn")

class ContextDecision(BaseModel):
    user_provided_info: bool = Field(description="True nếu user đề cập đến cân nặng, chiều cao, tuổi, hoặc mục tiêu ăn uống. False nếu user chỉ chào hỏi hoặc yêu cầu chung chung.")

    # Nếu user_provided_info = True:
    calculated_goals: Optional[MacroGoals] = Field(None, description="Kết quả tính toán NẾU đủ thông tin.")
    missing_info: List[str] = Field(default=[], description="Danh sách các thông tin còn thiếu để tính TDEE (VD: ['height', 'age']). Nếu đủ thì để trống.")

    reasoning: str = Field(description="Giải thích ngắn gọn tại sao đủ hoặc thiếu.")

def load_context_strict(state: AgentState):
    logger.info("---NODE: STRICT CONTEXT & CALCULATOR---")

    history = get_chat_history(state["messages"], max_tokens=1000)

    user_id = state.get("user_id", 1)

    system_prompt = """
    Bạn là Chuyên gia Dinh dưỡng AI.
    Nhiệm vụ: Phân tích hội thoại và xác định ngữ cảnh dữ liệu.

    LOGIC XỬ LÝ:
    1. Kiểm tra xem người dùng có đang cung cấp thông tin cá nhân (Cân nặng, Chiều cao, Tuổi, Giới tính, Mục tiêu) hoặc yêu cầu Calo cụ thể không?

    2. TRƯỜNG HỢP A: Người dùng KHÔNG cung cấp thông tin gì mới liên quan đến chỉ số cơ thể (chỉ hỏi "Gợi ý món ăn mặn"), cung cấp thông tin dinh dưỡng món ăn cũng vào trường hợp này (ví dụ "Gợi ý món ăn 400kcal).
       -> Trả về: user_provided_info = False. (Hệ thống sẽ tự dùng DB).

    3. TRƯỜNG HỢP B: Người dùng CÓ cung cấp thông tin (dù chỉ là 1 phần).
       -> Trả về: user_provided_info = True.
       -> Kiểm tra xem thông tin đã ĐỦ để tính TDEE chưa? (Cần đầy đủ (Weight, Height, Age, Gender, Activity) hoặc (Kcal, Protein, Lipid, Carbohydrate))
       -> NẾU THIẾU: Liệt kê các trường thiếu vào 'missing_info'.
       -> NẾU ĐỦ (hoặc user cho sẵn Target Kcal):
          - Hãy TÍNH TOÁN ngay lập tức 4 chỉ số: Kcal, Protein, Lipid, Carbohydrate.
          - Sử dụng công thức Mifflin-St Jeor cho BMR.
          - Phân bổ Macro theo chế độ ăn user mong muốn (hoặc mặc định 30P/30F/40C).
          - Trả về kết quả trong 'calculated_goals'.
    """

    try:
        chain = llm.with_structured_output(ContextDecision)
        input_messages = [SystemMessage(content=system_prompt)] + history
        decision = chain.invoke(input_messages)

        logger.info(f"   🤖 Decision: User Provided Info = {decision.user_provided_info}")
        logger.info(f"   📝 Missing Info: {decision.missing_info}")
        logger.info(f"   📝 Reasoning: {decision.reasoning}")

    except Exception as e:
        logger.info(f"⚠️ Lỗi LLM: {e}")
        return {"missing_fields": ["system_error"]}

    final_nutrition_goals = {}
    missing_fields = []

    if not decision.user_provided_info:
        logger.info("   💾 Dùng Profile Database.")
        nutrition_goals = get_user_by_id(user_id)
        restrictions = get_restrictions(nutrition_goals["healthStatus"])
        final_nutrition_goals = {**nutrition_goals, **restrictions}

    else:
        logger.info("   🚀 Dùng Profile Tạm thời (Session).")
        if decision.missing_info:
            logger.info(f"   ⛔ Còn thiếu: {decision.missing_info}")
            missing_fields = decision.missing_info
        elif decision.calculated_goals:
            goals = decision.calculated_goals
            logger.info(f"   ✅ Đã tính xong: {goals.targetcalories} Kcal")

            nutrition_goals = {
                "targetcalories": goals.targetcalories,
                "protein": goals.protein,
                "totalfat": goals.totalfat,
                "carbohydrate": goals.carbohydrate,
                "healthStatus": goals.heathStatus,
                "diet": goals.diet
            }
            restrictions = get_restrictions(nutrition_goals["healthStatus"])
            final_nutrition_goals = {**nutrition_goals, **restrictions}

    return {
        "user_profile": final_nutrition_goals,
        "missing_fields": missing_fields
    }