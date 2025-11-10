from langchain_core.messages import HumanMessage, SystemMessage, AIMessage, ToolMessage
from chatbot.agents.states.state import AgentState
from chatbot.models.llm_setup import llm
from chatbot.agents.tools.daily_meal_suggestion import daily_meal_suggestion

def suggest_meal_node(state: AgentState):
    print("---SUGGEST MEAL NODE---")

    # 🧠 Lấy dữ liệu từ state
    user_id = state.get("user_id", 0)
    question = state.get("messages")
    meals_to_generate = state.get("meals_to_generate", [])

    # 🧩 Chuẩn bị prompt mô tả yêu cầu
    system_prompt = """
    Bạn là một chuyên gia gợi ý thực đơn AI.
    Bạn không được tự trả lời hay đặt câu hỏi thêm.
    Nếu người dùng yêu cầu gợi ý món ăn, bắt buộc gọi tool 'daily_meal_suggestion'.
    với các tham số:
    - user_id: ID người dùng hiện tại
    - question: nội dung câu hỏi họ vừa hỏi
    - meals_to_generate: danh sách các bữa cần sinh thực đơn (nếu có)

    Nếu bạn không chắc bữa nào cần sinh, vẫn gọi tool này — phần xử lý sẽ lo chi tiết sau.
    """

    user_prompt = f"""
    Người dùng có ID: {user_id}
    Yêu cầu: "{question}"
    Danh sách các bữa cần gợi ý: {meals_to_generate}
    """

    # 🚀 Gọi LLM và Tools
    tools = [daily_meal_suggestion]
    llm_with_tools = llm.bind_tools(tools)
    
    response = llm_with_tools.invoke(
        [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ]
    )

    print("===== DEBUG =====")
    print("Response type:", type(response))
    print("Tool calls:", getattr(response, "tool_calls", None))
    print("Message content:", response.content)
    print("=================")

    if isinstance(response, AIMessage) and response.tool_calls:
        tool_call = response.tool_calls[0]
        tool_name = tool_call["name"]
        tool_args = tool_call["args"]
        tool_call_id = tool_call["id"]

        print(f"👉 Executing tool: {tool_name} with args: {tool_args}")

        # Bổ sung tham số nếu LLM quên
        tool_args.setdefault("user_id", user_id)
        tool_args.setdefault("question", question)
        tool_args.setdefault("meals_to_generate", meals_to_generate)

        if tool_name == "daily_meal_suggestion":
            result = daily_meal_suggestion.invoke(tool_args)
        elif tool_name == "fallback":
            result = {"message": "Không có tool phù hợp.", "reason": tool_args.get("reason", "")}
        else:
            result = {"message": f"Tool '{tool_name}' chưa được định nghĩa."}

        tool_message = ToolMessage(content=str(result), name=tool_name, tool_call_id=tool_call_id)
        return {"messages": state["messages"] + [response, tool_message], "response": result}
    return {"response": "Lỗi!!!"}
