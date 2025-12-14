from typing import Annotated, Optional, Literal, Sequence, TypedDict, List, Dict, Any
from langgraph.graph.message import add_messages
from langchain_core.messages import AnyMessage

class AgentState(TypedDict):
    user_id: Optional[str] = None
    question: str = ""

    topic: Optional[str] = None
    user_profile: Optional[Dict[str, Any]] = None

    missing_fields: List[str]
    is_valid: bool
    nutrition_goals: dict

    meals_to_generate: Optional[List[str]] = None
    suggested_meals: Optional[List[Dict[str, Any]]] = None

    candidate_pool: List[dict]
    selected_structure: List[dict]
    reason: Optional[str] = None
    final_menu: List[dict]

    response: Optional[str] = None
    messages: Annotated[List[AnyMessage], add_messages]

    food_old: Optional[Dict[str, Any]] = None

class SwapState(TypedDict):
    user_profile: Dict[str, Any]
    food_old: Dict[str, Any]
    candidates: List[Dict[str, Any]]
    top_candidates: List[Dict[str, Any]]
    best_replacement: Dict[str, Any]

__all__ = ["AgentState", "SwapState"]
