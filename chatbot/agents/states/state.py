from typing import Annotated, Optional, Literal, Sequence, TypedDict, List, Dict, Any
from langgraph.graph.message import add_messages

class AgentState(TypedDict):
    # ========== 1️⃣ Thông tin cơ bản ==========
    user_id: Optional[str]
    question: str

    # ========== 2️⃣ Ngữ cảnh hội thoại ==========
    topic: Optional[str]
    user_profile: Optional[Dict[str, Any]]

    # ========== 3️⃣ Gợi ý & lựa chọn món ăn ==========
    meal_intent: Optional[str]
    meals_to_generate: Optional[List[str]]
    suggested_meals: Optional[List[Dict[str, Any]]]
    selected_meals: Optional[List[Dict[str, Any]]]

    # ========== 4️⃣ Nhật ký & dinh dưỡng ==========
    today_log: Optional[List[Dict[str, Any]]]
    remaining: Optional[Dict[str, float]]

    # ========== 5️⃣ Kết quả & phản hồi ==========
    analysis_result: Optional[Dict[str, Any]]
    response: Optional[str]
    messages: Annotated[list, add_messages]

    # ========== 6️⃣ Mục tiêu & truy vấn ==========
    daily_goal: Optional[Dict[str, float]]
    meal_targets: Dict[str, Any]
    meal_queries: List[str]


__all__ = ["AgentState"]
