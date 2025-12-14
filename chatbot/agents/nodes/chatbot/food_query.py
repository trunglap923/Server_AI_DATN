from chatbot.agents.states.state import AgentState
from chatbot.agents.tools.food_retriever import query_constructor, docsearch
from langchain.retrievers.self_query.elasticsearch import ElasticsearchTranslator
from langchain.retrievers.self_query.base import SelfQueryRetriever
import logging

# --- Cấu hình logging ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def food_query(state: AgentState):
    logger.info("---FOOD QUERY---")

    messages = state["messages"]
    user_message = messages[-1].content if messages else state.question

    suggested_meals = []

    prompt = f"""
    Câu hỏi: "{user_message}".
    Hãy tìm các món ăn phù hợp với yêu cầu này.
    """

    query_ans = query_constructor.invoke(prompt)
    food_retriever = SelfQueryRetriever(
        query_constructor=query_constructor,
        vectorstore=docsearch,
        structured_query_translator=ElasticsearchTranslator(),
        search_kwargs={"k": 2},
    )
    logger.info(f"🔍 Dạng truy vấn: {food_retriever.structured_query_translator.visit_structured_query(structured_query=query_ans)}")

    foods = food_retriever.invoke(prompt)
    logger.info(f"🔍 Kết quả truy vấn: ")
    for i, food in enumerate(foods):
        logger.info(f"{i} - {food.metadata['name']}")
        suggested_meals.append(food)

    return {"suggested_meals": suggested_meals}