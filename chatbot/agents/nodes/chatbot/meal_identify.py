from langchain.prompts import ChatPromptTemplate
import json
from pydantic import BaseModel, Field
from chatbot.agents.states.state import AgentState
from chatbot.models.llm_setup import llm
from typing import List
import logging

# --- Cấu hình logging ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MealIntent(BaseModel):
    meals_to_generate: List[str] = Field(
        description="Danh sách các bữa được người dùng muốn gợi ý: ['sáng', 'trưa', 'tối']."
    )
    
def meal_identify(state: AgentState):
    logger.info("---MEAL IDENTIFY---")
    messages = state["messages"]
    user_message = messages[-1].content if messages else state.question
    
    structured_llm = llm.with_structured_output(MealIntent)

    system = """
    Bạn là chuyên gia phân tích yêu cầu dinh dưỡng.
    Nhiệm vụ: Đọc câu hỏi người dùng và trích xuất danh sách các bữa ăn họ muốn gợi ý.
    Chỉ được chọn trong các giá trị: "sáng", "trưa", "tối".
    Nếu người dùng nói "cả ngày", hãy trả về ["sáng", "trưa", "tối"].
    """

    prompt = ChatPromptTemplate.from_messages([
        ("system", system),
        ("human", "{question}"),
    ])
    
    chain = prompt | structured_llm

    try:
        result = chain.invoke({"question": user_message})

        if not result:
            logger.info("⚠️ Model không trả về định dạng đúng, dùng mặc định.")
            meals = ["sáng", "trưa", "tối"]
        else:
            meals = result.meals_to_generate

    except Exception as e:
        logger.info(f"⚠️ Lỗi Parse JSON: {e}")
        meals = ["sáng", "trưa", "tối"]

    logger.info("Bữa cần gợi ý: " + ", ".join(meals))

    return {
        "meals_to_generate": meals
    }
