from pydantic import BaseModel
from typing import List, Dict, Any, Optional

class MealSuggestionRequest(BaseModel):
    user_id: str
    question: str = ""
    meals_to_generate: List[str]
    user_profile: Optional[Dict[str, Any]] = None

class FoodReplaceRequest(BaseModel):
    user_id: str
    food_old: Dict[str, Any]

class ChatbotRequest(BaseModel):
    user_id: str
    thread_id: str
    message: str
