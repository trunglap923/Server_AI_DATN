from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from langchain_core.messages import HumanMessage
from chatbot.agents.graphs.chatbot_graph import workflow_chatbot
import logging

# --- Cấu hình logging ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Định nghĩa request body ---
class ChatRequest(BaseModel):
    user_id: str
    thread_id: str
    message: str

# --- Tạo router ---
router = APIRouter(
    prefix="/chat",
    tags=["Chatbot"]
)

try:
    chatbot_app = workflow_chatbot()
except Exception as e:
    logger.error(f"❌ Failed to compile Chatbot Graph: {e}")
    raise e

# --- Route xử lý chat ---
@router.post("/")
def chat(request: ChatRequest):
    try:
        logger.info(f"Nhận được tin nhắn chat từ user: {request.user_id}")
        config = {"configurable": {"thread_id": request.thread_id}}

        initial_state = {
            "user_id": request.user_id,
            "messages": [HumanMessage(content=request.message)]
        }

        final_state = chatbot_app.invoke(initial_state, config=config)

        messages = final_state.get("messages", [])
        if messages and len(messages) > 0:
            response_content = messages[-1].content
        else:
            response_content = "Không có kết quả trả về."

        return {"response": response_content}

    except Exception as e:
        logger.error(f"Lỗi chatbot: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Lỗi chatbot: {str(e)}")