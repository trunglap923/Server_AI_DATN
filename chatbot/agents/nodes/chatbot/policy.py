from chatbot.agents.states.state import AgentState
from langchain_core.messages import AIMessage, SystemMessage, HumanMessage
from chatbot.models.llm_setup import llm
from chatbot.agents.tools.info_app_retriever import policy_retriever
import logging

# --- Cấu hình logging ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def policy(state: AgentState):
    logger.info("---POLICY---")
    messages = state["messages"]
    question = messages[-1].content if messages else state.question

    try:
        docs = policy_retriever.invoke(question)

        if not docs:
            return {"messages": [AIMessage(content="Xin lỗi, tôi không tìm thấy thông tin chính sách liên quan đến câu hỏi của bạn trong hệ thống.")]}

        context_text = "\n\n".join([d.page_content for d in docs])

    except Exception as e:
        logger.info(f"⚠️ Lỗi Policy Retriever: {e}")
        return {"messages": [AIMessage(content="Hệ thống tra cứu chính sách đang gặp sự cố.")]}

    system_prompt = f"""
Bạn là Trợ lý AI hỗ trợ Chính sách & Quy định của Ứng dụng.

NHIỆM VỤ:
Trả lời câu hỏi người dùng CHỈ DỰA TRÊN thông tin được cung cấp dưới đây.

THÔNG TIN THAM KHẢO:
{context_text}

QUY TẮC AN TOÀN:
1. Nếu thông tin không có trong phần tham khảo, hãy trả lời: "Xin lỗi, hiện tại trong tài liệu chính sách không đề cập đến vấn đề này."
2. Không được tự bịa ra chính sách hoặc đoán mò.
3. Trả lời ngắn gọn, đi thẳng vào vấn đề.
    """
    logger.info(f"Prompt gửi đến LLM cho chính sách: {system_prompt}")

    try:
        response = llm.invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=question)
        ])

        return {"messages": [response]}

    except Exception as e:
        return {"messages": [AIMessage(content="Lỗi khi tạo câu trả lời.")]}
