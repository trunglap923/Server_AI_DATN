from langgraph.graph import StateGraph, START, END
from chatbot.agents.states.state import AgentState
from langgraph.checkpoint.memory import MemorySaver
from chatbot.knowledge.field_requirement import TOPIC_REQUIREMENTS
from chatbot.agents.nodes.chatbot import (
    classify_topic,
    meal_identify,
    suggest_meal_node,
    generate_final_response,
    food_suggestion,
    select_food_plan,
    food_query,
    select_food,
    general_chat,
    policy,
    ask_missing_info,
    load_context_strict,
    universal_validator
)

def workflow_chatbot():
    workflow = StateGraph(AgentState)

    workflow.add_node("classify_topic", classify_topic)
    workflow.add_node("validator", universal_validator)
    workflow.add_node("load_context", load_context_strict)
    workflow.add_node("ask_info", ask_missing_info)

    workflow.add_node("meal_identify", meal_identify)
    workflow.add_node("suggest_meal_node", suggest_meal_node)
    workflow.add_node("generate_final_response", generate_final_response)
    
    workflow.add_node("food_suggestion", food_suggestion)
    workflow.add_node("select_food_plan", select_food_plan)
    
    workflow.add_node("food_query", food_query)
    workflow.add_node("select_food", select_food)
    
    workflow.add_node("general_chat", general_chat)
    
    workflow.add_node("policy", policy)

    workflow.add_edge(START, "classify_topic")

    workflow.add_conditional_edges(
        "classify_topic",
        route_initial,
        {
            "policy": "policy",
            "food_query": "food_query",
            "general_chat": "general_chat",
            "load_context": "load_context"
        }
    )

    workflow.add_edge("load_context", "validator")

    workflow.add_conditional_edges(
        "validator",
        route_post_validation,
        {
            "ask_info": "ask_info",
            "meal_suggestion": "meal_identify",
            "food_suggestion": "food_suggestion",
            # "food_query": "food_query",
            # "general_chat": "general_chat",
            # "policy": "policy",
        }
    )

    workflow.add_edge("ask_info", END)

    workflow.add_edge("meal_identify", "suggest_meal_node")
    workflow.add_edge("suggest_meal_node", "generate_final_response")
    workflow.add_edge("generate_final_response", END)

    workflow.add_edge("food_suggestion", "select_food_plan")
    workflow.add_edge("select_food_plan", END)

    workflow.add_edge("food_query", "select_food")
    workflow.add_edge("select_food", END)

    workflow.add_edge("policy", END)
    
    workflow.add_edge("general_chat", END)

    memory = MemorySaver()
    app = workflow.compile(checkpointer=memory)
    
    return app

def route_initial(state: AgentState):
    topic = state.get("topic")
    non_empty_keys = [key for key, value in TOPIC_REQUIREMENTS.items() if value]
    if topic in non_empty_keys:
        return "load_context"
    return topic

def route_post_validation(state: AgentState):
    if not state.get("is_valid"):
        return "ask_info"

    topic = state.get("topic")
    return topic
