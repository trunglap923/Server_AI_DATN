from chatbot.agents.states.state import AgentState
from chatbot.models.llm_setup import llm
from langchain.schema.messages import SystemMessage, HumanMessage
from chatbot.utils.chat_history import get_chat_history
import logging

# --- Cấu hình logging ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def general_chat(state: AgentState):
    logger.info("---GENERAL CHAT---")

    history = get_chat_history(state["messages"], max_tokens=1000)

    system_text = """
    Bạn là một chuyên gia dinh dưỡng và ẩm thực AI.
    Hãy trả lời các câu hỏi về:
    - món ăn, thành phần, dinh dưỡng, calo, protein, chất béo, carb,
    - chế độ ăn (ăn chay, keto, giảm cân, tăng cơ...),
    - sức khỏe, lối sống, chế độ tập luyện liên quan đến ăn uống.
    - chức năng, điều khoản, chính sách của ứng dụng.

    Quy tắc:
    - Không trả lời các câu hỏi ngoài chủ đề này (hãy từ chối lịch sự).
    - Giải thích ngắn gọn, tự nhiên, rõ ràng.
    - Dựa vào lịch sử trò chuyện để trả lời mạch lạc nếu có câu hỏi nối tiếp.
    """

    messages_to_send = [SystemMessage(content=system_text)] + history
    
    try:
        response = llm.invoke(messages_to_send)
        logger.info(f"🤖 AI Response: {response.content}")
        return {"messages": [response]}
    except Exception as e:
        logger.info(f"⚠️ Lỗi General Chat: {e}")
        return {"messages": []}