from chatbot.agents.states.state import AgentState
from chatbot.models.llm_setup import llm
from langchain.schema.messages import SystemMessage, HumanMessage
from chatbot.utils.user_profile import get_user_by_id

def general_chat(state: AgentState):
    print("---GENERAL CHAT---")

    user_id = state.get("user_id", {})
    messages = state["messages"]
    user_message = messages[-1].content if messages else state.question

    user_profile = get_user_by_id(user_id)

    system_prompt = f"""
    Bạn là một chuyên gia dinh dưỡng và ẩm thực AI.
    Hãy trả lời các câu hỏi về:
    - món ăn, thành phần, dinh dưỡng, calo, protein, chất béo, carb,
    - chế độ ăn (ăn chay, keto, giảm cân, tăng cơ...),
    - sức khỏe, lối sống, chế độ tập luyện liên quan đến ăn uống.
    Một số thông tin về người dùng có thể dùng đến như sau:
    - Tổng năng lượng mục tiêu: {user_profile['kcal']} kcal/ngày
        - Protein: {user_profile['protein']}g
        - Chất béo (lipid): {user_profile['lipid']}g
        - Carbohydrate: {user_profile['carbohydrate']}g
        - Chế độ ăn: {user_profile['khẩu phần']}
    Không trả lời các câu hỏi ngoài chủ đề này.
    Giải thích ngắn gọn, tự nhiên, rõ ràng.
    """

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_message),
    ]

    response = llm.invoke(messages)

    print(response.content if hasattr(response, "content") else response)

    return {"response": response.content}