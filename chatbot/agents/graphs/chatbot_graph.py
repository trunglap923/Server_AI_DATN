from langgraph.graph import StateGraph, START, END
from chatbot.agents.states.state import AgentState

# Import các node
from chatbot.agents.nodes.classify_topic import classify_topic, route_by_topic
from chatbot.agents.nodes.meal_identify import meal_identify
from chatbot.agents.nodes.suggest_meal_node import suggest_meal_node
from chatbot.agents.nodes.food_query import food_query
from chatbot.agents.nodes.select_food_plan import select_food_plan
from chatbot.agents.nodes.general_chat import general_chat

def workflow_chatbot() -> StateGraph:
    workflow_chatbot = StateGraph(AgentState)

    workflow_chatbot.add_node("classify_topic", classify_topic)
    workflow_chatbot.add_node("meal_identify", meal_identify)
    workflow_chatbot.add_node("suggest_meal_node", suggest_meal_node)
    workflow_chatbot.add_node("food_query", food_query)
    workflow_chatbot.add_node("select_food_plan", select_food_plan)
    workflow_chatbot.add_node("general_chat", general_chat)

    workflow_chatbot.add_edge(START, "classify_topic")

    workflow_chatbot.add_conditional_edges(
        "classify_topic",
        route_by_topic,
        {
            "meal_identify": "meal_identify",
            "food_query": "food_query",
            "general_chat": "general_chat",
        }
    )

    workflow_chatbot.add_edge("meal_identify", "suggest_meal_node")
    workflow_chatbot.add_edge("suggest_meal_node", END)

    workflow_chatbot.add_edge("food_query", "select_food_plan")
    workflow_chatbot.add_edge("select_food_plan", END)

    workflow_chatbot.add_edge("general_chat", END)

    graph = workflow_chatbot.compile()
    return graph
