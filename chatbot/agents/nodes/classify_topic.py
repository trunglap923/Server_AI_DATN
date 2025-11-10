from langchain.prompts import PromptTemplate
import json
from pydantic import BaseModel, Field
from chatbot.agents.states.state import AgentState
from chatbot.models.llm_setup import llm

class Topic(BaseModel):
    name: str = Field(
        description=(
            "Tên chủ đề mà người dùng đang hỏi. "
            "Các giá trị hợp lệ: 'nutrition_analysis', 'meal_suggestion', 'general_chat'."
        )
    )

def classify_topic(state: AgentState):
    print("---CLASSIFY TOPIC---")
    llm_with_structure_op = llm.with_structured_output(Topic)

    prompt = PromptTemplate(
        template="""
        Bạn là bộ phân loại chủ đề câu hỏi người dùng trong hệ thống chatbot dinh dưỡng.

        Nhiệm vụ:
        - Phân loại câu hỏi vào một trong các nhóm:
            1. "meal_suggestion": khi người dùng muốn gợi ý thực đơn cho một bữa ăn, khẩu phần, hoặc chế độ ăn (chỉ cho bữa ăn, không cho món ăn đơn lẻ).
            2. "food_query": khi người dùng tìm kiếm, gợi ý một món ăn hoặc muốn biết thành phần dinh dưỡng của món ăn hoặc khẩu phần cụ thể.
            3. "general_chat": khi câu hỏi không thuộc hai nhóm trên.

        Câu hỏi người dùng: {question}

        Hãy trả lời dưới dạng JSON phù hợp với schema sau:
        {format_instructions}
        """
    )

    messages = state["messages"]
    user_message = messages[-1].content if messages else state.question

    format_instructions = json.dumps(llm_with_structure_op.output_schema.model_json_schema(), ensure_ascii=False, indent=2)

    chain = prompt | llm_with_structure_op

    topic_result = chain.invoke({
        "question": user_message,
        "format_instructions": format_instructions
    })

    print("Topic:", topic_result.name)

    return {"topic": topic_result.name}

def route_by_topic(state: AgentState):
    topic = state["topic"]
    if topic == "meal_suggestion":
        return "meal_identify"
    elif topic == "food_query":
        return "food_query"
    else:
        return "general_chat"
    