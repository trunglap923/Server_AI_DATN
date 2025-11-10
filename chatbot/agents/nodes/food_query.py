from chatbot.agents.states.state import AgentState
from chatbot.utils.user_profile import get_user_by_id
from chatbot.agents.tools.food_retriever import food_retriever, food_retriever_top3, query_constructor


def food_query(state: AgentState):
    print("---FOOD QUERY---")

    user_id = state.get("user_id", {})
    messages = state["messages"]
    user_message = messages[-1].content if messages else state.question

    user_profile = get_user_by_id(user_id)

    suggested_meals = []

    prompt = f"""
    Người dùng có khẩu phần: {user_profile["khẩu phần"]}.
    Câu hỏi: "{user_message}".
    Hãy tìm các món ăn phù hợp với khẩu phần và yêu cầu này, cho phép sai lệch không quá 20%.
    """

    query_ans = query_constructor.invoke(prompt)
    print(f"🔍 Dạng truy vấn: {food_retriever.structured_query_translator.visit_structured_query(structured_query=query_ans)}")
    foods = food_retriever_top3.invoke(prompt)
    print(f"🔍 Kết quả truy vấn: ")
    for i, food in enumerate(foods):
        print(f"{i} - {food.metadata['name']}")
        suggested_meals.append(food)

    return {"suggested_meals": suggested_meals, "user_profile": user_profile}