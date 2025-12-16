from chatbot.agents.states.state import AgentState
from chatbot.agents.tools.food_retriever import query_constructor, food_retriever
import logging

# --- Cấu hình logging ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def food_suggestion(state: AgentState):
    logger.info("---FOOD QUERY SUGGESTION---")

    user_id = state.get("user_id", {})
    messages = state["messages"]
    user_message = messages[-1].content if messages else state.question

    user_profile = state.get("user_profile", {})

    suggested_meals = []

    prompt = f"""
    Người dùng có khẩu phần: {user_profile["diet"]}.
    Câu hỏi: "{user_message}".
    Hãy tìm các món ăn phù hợp với khẩu phần và yêu cầu này, cho phép sai lệch không quá 20%.
    """

    # query_ans = query_constructor.invoke(prompt)
    # logger.info(f"🔍 Dạng truy vấn: {food_retriever.structured_query_translator.visit_structured_query(structured_query=query_ans)}")
    foods = food_retriever.invoke(prompt)
    logger.info(f"🔍 Kết quả truy vấn: ")
    for i, food in enumerate(foods):
        logger.info(f"{i} - {food.metadata['name']}")
        suggested_meals.append(food)

    return {"suggested_meals": suggested_meals, "user_profile": user_profile}