from langchain.prompts import PromptTemplate
import json
from pydantic import BaseModel, Field
from chatbot.agents.states.state import AgentState
from chatbot.models.llm_setup import llm
from typing import List

class MealIntent(BaseModel):
    intent: str = Field(
        description=(
            "Loại yêu cầu của người dùng, có thể là:\n"
            "- 'full_day_meal': khi người dùng chưa ăn bữa nào và muốn gợi ý thực đơn cho cả ngày.\n"
            "- 'not_full_day_meal': khi người dùng đã ăn một vài bữa và muốn gợi ý một bữa cụ thể hoặc các bữa còn lại."
        )
    )
    meals_to_generate: List[str] = Field(
        description="Danh sách các bữa được người dùng muốn gợi ý: ['sáng', 'trưa', 'tối']."
    )
    
    
def meal_identify(state: AgentState):
    print("---MEAL IDENTIFY---")

    llm_with_structure_op = llm.with_structured_output(MealIntent)

    # Lấy câu hỏi mới nhất từ lịch sử hội thoại
    messages = state["messages"]
    user_message = messages[-1].content if messages else state.question

    format_instructions = json.dumps(llm_with_structure_op.output_schema.model_json_schema(), ensure_ascii=False, indent=2)

    prompt = PromptTemplate(
        template="""
        Bạn là bộ phân tích yêu cầu gợi ý bữa ăn trong hệ thống chatbot dinh dưỡng.

        Dựa trên câu hỏi của người dùng, hãy xác định:
        1. Người dùng muốn gợi ý cho **cả ngày**, **một hoặc một vài bữa cụ thể**.
        2. Danh sách các bữa người dùng muốn gợi ý (nếu có).

        Quy tắc:
        - Nếu người dùng muốn gợi ý thực đơn cho cả ngày → intent = "full_day_meal".
        - Nếu họ nói đã ăn một bữa nào đó, muốn gợi ý một hoặc các bữa còn lại → intent = "not_full_day_meal".
        - Các bữa người dùng có thể muốn gợi ý: ["sáng", "trưa", "tối"].

        Câu hỏi người dùng: {question}

        Hãy xuất kết quả dưới dạng JSON theo schema sau:
        {format_instructions}
        """
    )

    chain = prompt | llm_with_structure_op

    result = chain.invoke({
        "question": user_message,
        "format_instructions": format_instructions
    })

    print("Bữa cần gợi ý: " + ", ".join(result.meals_to_generate))

    return {
        "meal_intent": result.intent,
        "meals_to_generate": result.meals_to_generate,
    }
