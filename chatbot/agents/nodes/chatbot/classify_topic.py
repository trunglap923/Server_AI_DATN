from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from pydantic import BaseModel, Field
from chatbot.agents.states.state import AgentState
from chatbot.models.llm_setup import llm
from chatbot.utils.chat_history import get_chat_history
from chatbot.knowledge.field_requirement import TOPIC_REQUIREMENTS
import logging

# --- Cấu hình logging ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Topic(BaseModel):
    name: str = Field(
        description=(
            "Tên chủ đề mà người dùng đang hỏi. "
            "Các giá trị hợp lệ: 'meal_suggestion', 'food_suggestion', food_query, 'policy', 'general_chat'."
        )
    )

def classify_topic(state: AgentState):
    print("---CLASSIFY TOPIC ---")
    all_messages = state["messages"]
    
    question = all_messages[-1].content
    history_messages = all_messages[:-1]

    system_msg = """
    Bạn là bộ điều hướng thông minh.
    Nhiệm vụ: Phân loại câu hỏi của người dùng vào nhóm thích hợp.

    CÁC NHÓM CHỦ ĐỀ:
    1. "meal_suggestion": Gợi ý thực đơn ăn uống các bữa.
    2. "food_suggestion": Gợi ý một món ăn cụ thể.
    3. "food_query": Hỏi thông tin dinh dưỡng một món ăn cụ thể.
    4. "policy": Khi người dùng hỏi về thông tin, đặc điểm, quy định, chính sách, hướng dẫn sử dụng MỚI mà chưa có trong lịch sử (liên quan đến app).
    5. "general_chat":
       - Chào hỏi xã giao.
       - Các câu hỏi sức khỏe chung chung.
       - QUAN TRỌNG: Các câu hỏi NỐI TIẾP (Follow-up) yêu cầu giải thích, làm rõ thông tin ĐÃ CÓ trong lịch sử hội thoại (Ví dụ: "Giải thích ý đó", "Tại sao lại thế", "Cụ thể hơn đi").

    NGUYÊN TẮC ƯU TIÊN:
    - Nếu câu hỏi mơ hồ (VD: "ý thứ 2 là gì", "nó hoạt động sao"), hãy kiểm tra lịch sử.
    - Nếu câu trả lời cho câu hỏi đó ĐÃ NẰM trong tin nhắn trước của AI -> Chọn "general_chat" (để AI tự trả lời bằng trí nhớ).
    - Chỉ chọn các topic chuyên biệt (policy/food...) khi cần tra cứu dữ liệu MỚI bên ngoài.
    """

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_msg),
        MessagesPlaceholder(variable_name="history"), # Bối cảnh chat
        ("human", "{input}")                          # Câu hỏi MỚI CẦN PHÂN LOẠI
    ])

    classifier_llm = llm.with_structured_output(Topic)
    chain = prompt | classifier_llm

    recent_messages = get_chat_history(state["messages"], max_tokens=500)

    try:
        topic_result = chain.invoke({
            "history": recent_messages, # Lịch sử chat (MessagesPlaceholder)
            "input": question           # Câu hỏi mới (HumanMessage)
        })
        topic_name = topic_result.name
    except Exception as e:
        print(f"⚠️ Lỗi phân loại: {e}")
        topic_name = "general_chat"

    print(f"Topic detected: {topic_name}")
    return {"topic": topic_name}    