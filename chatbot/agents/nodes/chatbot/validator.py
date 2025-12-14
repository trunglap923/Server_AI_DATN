
from chatbot.agents.states.state import AgentState
from chatbot.knowledge.field_requirement import TOPIC_REQUIREMENTS
import logging

# --- Cấu hình logging ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def universal_validator(state: AgentState):
    print("---NODE: UNIVERSAL VALIDATOR---")

    # 1. Lấy dữ liệu
    topic = state.get("topic", "general_chat")
    goals = state.get("user_profile", {})
    missing_from_prev = state.get("missing_fields", [])

    # 2. Xác định yêu cầu của Topic hiện tại
    required_fields = TOPIC_REQUIREMENTS.get(topic, [])

    # 3. Logic Kiểm Tra
    final_missing = []
    # Trường hợp A: Nếu bước trước LLM đã báo thiếu
    if missing_from_prev:
        final_missing.extend(missing_from_prev)
    # Trường hợp B: Kiểm tra lại các trường bắt buộc của topic
    for field in required_fields:
        value = goals.get(field)

        if value is None:
            final_missing.append(field)
        elif isinstance(value, (int, float)) and value <= 0:
            final_missing.append(field)
        elif isinstance(value, str) and not value.strip():
            final_missing.append(field)

    final_missing = list(set(final_missing))

    if final_missing:
        logger.info(f"   ⛔ Topic '{topic}' thiếu: {final_missing}")
        return {"is_valid": False, "missing_fields": final_missing}

    logger.info(f"   ✅ Topic '{topic}' đủ thông tin. Pass.")
    return {"is_valid": True, "missing_fields": []}