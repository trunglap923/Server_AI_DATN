from pydantic import BaseModel, Field
from typing import Dict, Any

class FoodItemPayload(BaseModel):
    text_for_embedding: str = Field(..., description="Văn bản dùng để tạo embedding cho món ăn")
    metadata: Dict[str, Any] = Field(..., description="Metadata chi tiết của món ăn (bao gồm meal_id)")
