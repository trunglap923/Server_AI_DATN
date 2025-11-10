from langgraph.graph import StateGraph, START, END
from chatbot.agents.states.state import AgentState

# Import các node
from chatbot.agents.tools.daily_meal_functions import get_user_profile, generate_food_plan, generate_meal_plan

def workflow_meal_suggestion() -> StateGraph:
    workflow = StateGraph(AgentState)

    workflow.add_node("Get_User_Profile", get_user_profile)
    workflow.add_node("Generate_Food_Plan", generate_food_plan)
    workflow.add_node("Generate_Meal_Plan", generate_meal_plan)

    workflow.set_entry_point("Get_User_Profile")

    workflow.add_edge("Get_User_Profile", "Generate_Food_Plan")
    workflow.add_edge("Generate_Food_Plan", "Generate_Meal_Plan")
    workflow.add_edge("Generate_Meal_Plan", END)

    graph = workflow.compile()
    return graph
