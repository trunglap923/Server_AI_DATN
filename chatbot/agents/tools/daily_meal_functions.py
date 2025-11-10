import logging
from typing import List, Dict, Any

from chatbot.agents.states.state import AgentState
from chatbot.agents.tools.food_retriever import query_constructor, food_retriever
from langgraph.graph import END, StateGraph
from chatbot.models.llm_setup import llm
from langchain.tools import tool
from chatbot.utils.user_profile import get_user_by_id

# --- Cấu hình logging ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_user_profile(state: AgentState) -> Dict[str, Any]:
    """
    Node: Lấy profile người dùng và chuẩn hóa key.
    """
    logger.info("--- GET_USER_PROFILE ---")
    user_id = state.get("user_id", "")
    user_profile = get_user_by_id(user_id)

    # Chuẩn hóa khóa
    mapping = {"fat": "lipid", "carbs": "carbohydrate", "protein": "protein",
               "kcal": "kcal", "lipid": "lipid", "carbohydrate": "carbohydrate"}
    normalized_profile = {mapping.get(k.lower(), k.lower()): v for k, v in user_profile.items()}

    # Fallback default nếu thiếu
    defaults = {"kcal": 1700, "protein": 120, "lipid": 56, "carbohydrate": 170, "khẩu phần": "ăn chay"}
    for key, val in defaults.items():
        normalized_profile.setdefault(key, val)

    logger.info(f"User profile chuẩn hóa: {normalized_profile}")

    return {"user_profile": normalized_profile, "daily_goal": normalized_profile, "suggested_meals": []}

# --- Generate food plan ---
def generate_food_plan(state: AgentState) -> Dict[str, Any]:
    logger.info("--- GENERATE_FOOD_PLAN ---")
    meals_to_generate: List[str] = state.get("meals_to_generate", [])
    user_profile: Dict[str, Any] = state.get("user_profile", {})

    if not meals_to_generate:
        logger.warning("meals_to_generate rỗng, sử dụng mặc định ['sáng', 'trưa', 'tối']")
        meals_to_generate = ["sáng", "trưa", "tối"]

    meals_text = ", ".join(meals_to_generate)

    query_text = (
        f"Tìm các món ăn phù hợp với người dùng có chế độ ăn: {user_profile.get('khẩu phần', 'ăn chay')}. "
        f"Ưu tiên món phổ biến, cân bằng dinh dưỡng, cho bữa {meals_text}."
    )
    logger.info(f"Query: {query_text}")

    try:
        foods = food_retriever.invoke(query_text)
    except Exception as e:
        logger.error(f"Lỗi khi truy vấn món ăn: {e}")
        foods = []

    suggested_meals = [food.metadata for food in foods] if foods else []
    logger.info(f"Số món được gợi ý: {len(suggested_meals)}")

    return {"suggested_meals": suggested_meals}

def generate_meal_plan(state: AgentState):
    logger.info("--- GENERATE_MEAL_PLAN ---")
    user_profile = state.get("user_profile", {})
    suggested_meals = state.get("suggested_meals", [])
    meals_to_generate = state.get("meals_to_generate", [])
    question = state.get("question", "Hãy tạo thực đơn cho tôi.")

    meals_text = ", ".join(meals_to_generate)

    suggested_meals_text = "\n".join(
        [f"- {meal['name']}: {meal.get('kcal', 0)} kcal, "
         f"{meal.get('protein', 0)}g protein, "
         f"{meal.get('lipid', 0)}g chất béo, "
         f"{meal.get('carbohydrate', 0)}g carbohydrate"
         for meal in suggested_meals]
    ) if suggested_meals else "Chưa có món ăn gợi ý."

    prompt = f"""
        Bạn có thể sử dụng thông tin người dùng có hồ sơ dinh dưỡng sau nếu cần thiết cho câu hỏi của người dùng:
        - Tổng năng lượng mục tiêu: {user_profile['kcal']} kcal/ngày
        - Protein: {user_profile['protein']}g
        - Chất béo (lipid): {user_profile['lipid']}g
        - Carbohydrate: {user_profile['carbohydrate']}g
        - Chế độ ăn: {user_profile['khẩu phần']}

        Câu hỏi của người dùng: "{question}"

        Các bữa cần xây dựng:
        {meals_text}

        Danh sách món ăn hiện có để chọn:
        {suggested_meals_text}

        Yêu cầu:
        1. Hãy tổ hợp các món ăn trên để tạo thực đơn cho từng bữa (chỉ chọn trong danh sách có sẵn).
        2. Mỗi bữa gồm 1 đến 3 món, tổng năng lượng và dinh dưỡng xấp xỉ giá trị yêu cầu của bữa đó (±15%).
        3. Nếu cần, hãy ước tính khẩu phần mỗi món (ví dụ: 0.5 khẩu phần hoặc 1.2 khẩu phần) để đạt cân bằng chính xác.
        4. Đảm bảo tổng giá trị dinh dưỡng toàn ngày gần với hồ sơ người dùng.
        5. Chỉ chọn những món phù hợp với chế độ ăn: {user_profile['khẩu phần']}.
    """

    logger.info(prompt)
    
    try:
        result = llm.invoke(prompt, timeout=60)
        response_content = getattr(result, "content", str(result))
    except Exception as e:
        logger.error(f"Lỗi khi gọi LLM: {e}")
        response_content = "Không thể tạo thực đơn lúc này, vui lòng thử lại sau."

    logger.info("Meal plan suggestion generated.")
    return {"response": response_content}