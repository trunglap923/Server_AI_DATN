from chatbot.agents.states.state import SwapState
from chatbot.agents.tools.food_retriever import food_retriever
from chatbot.agents.nodes.app_functions.generate_candidates import generate_numerical_constraints
import logging

# --- Cấu hình logging ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def find_replacement_candidates(state: SwapState):
    logger.info("---NODE: FIND REPLACEMENTS (SELF QUERY)---")
    food_old = state.get("food_old")
    profile = state.get("user_profile", {})
    
    if not food_old:
        logger.warning("⚠️ Không tìm thấy thông tin món cũ (food_old).")
        return {"candidates": []}

    diet_mode = profile.get('diet', '')       # VD: Chế độ HighProtein
    restrictions = profile.get('limitFood', '') # VD: Dị ứng sữa, Thuần chay
    health_status = profile.get('healthStatus', '') # VD: Suy thận

    constraint_prompt = ""
    if restrictions:
        constraint_prompt += f"Yêu cầu bắt buộc: {restrictions}. "
    if health_status:
        constraint_prompt += f"Phù hợp người bệnh: {health_status}. "
    if diet_mode:
        constraint_prompt += f"Chế độ: {diet_mode}."

    # 1. Trích xuất ngữ cảnh từ món cũ
    role = food_old.get("role", "main")       # VD: main, side, carb
    meal_type = food_old.get("assigned_meal", "trưa") # VD: trưa
    old_name = food_old.get("name", "")
    numerical_query = generate_numerical_constraints(profile, meal_type)

    # 2. Xây dựng Query tự nhiên để SelfQueryRetriever hiểu
    query = (
        f"Tìm các món ăn đóng vai trò '{role}' phù hợp cho bữa '{meal_type}'. "
        f"Khác với món '{old_name}'. "
        f"{constraint_prompt}"
    )

    if numerical_query:
        query += f"Yêu cầu: {numerical_query}"
    logger.info(f"🔎 Query: {query}")

    # 3. Gọi Retriever
    try:
        docs = food_retriever.invoke(query)
    except Exception as e:
        logger.info(f"⚠️ Lỗi Retriever: {e}")
        return {"candidates": []}

    # 4. Lọc sơ bộ (Python Filter)
    candidates = []
    for doc in docs:
        item = doc.metadata.copy()
        if item.get("name") == old_name: continue
        
        item["target_role"] = role
        item["target_meal"] = meal_type
        candidates.append(item)

    logger.info(f"📚 Tìm thấy {len(candidates)} ứng viên tiềm năng.")
    return {"candidates": candidates}