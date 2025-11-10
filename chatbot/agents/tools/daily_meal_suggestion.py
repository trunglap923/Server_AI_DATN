import logging
from typing import List, Dict, Any

from chatbot.agents.states.state import AgentState
from chatbot.agents.tools.food_retriever import query_constructor, food_retriever
from langgraph.graph import END, StateGraph
from chatbot.models.llm_setup import llm
from langchain.tools import tool
from chatbot.utils.user_profile import get_user_by_id
from chatbot.agents.graphs.meal_suggestion_graph import workflow_meal_suggestion

# --- Cấu hình logging ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@tool("daily_meal_suggestion", return_direct=True)
def daily_meal_suggestion(user_id: str, question: str, meals_to_generate: list):
    """
    Sinh thực đơn hàng ngày hoặc cho các bữa cụ thể dựa trên hồ sơ dinh dưỡng người dùng,
    câu hỏi và danh sách các bữa cần gợi ý.

    Args:
        user_id (str): ID của người dùng để lấy thông tin hồ sơ dinh dưỡng tương ứng từ hệ thống.
        question (str): Câu hỏi hoặc mong muốn cụ thể của người dùng
                        (VD: "Tôi muốn gợi ý bữa trưa và bữa tối").
        meals_to_generate (list): Danh sách các bữa cần sinh thực đơn, ví dụ ["trưa", "tối"].
    """

    logger.info(f"Tool daily_meal_suggestion invoked: user_id={user_id}, meals={meals_to_generate}")
    if not isinstance(meals_to_generate, list):
        logger.warning("meals_to_generate không phải list, ép về list")
        meals_to_generate = list(meals_to_generate)

    workflow  = workflow_meal_suggestion()

    # 🧩 Truyền vào graph để xử lý
    result = workflow .invoke({
        "user_id": user_id,
        "question": question,
        "meals_to_generate": meals_to_generate,
    })

    return result["response"]

