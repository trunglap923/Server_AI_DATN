from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from langchain_core.messages import HumanMessage
from app.core.container import container
from app.schema.dtos import ChatbotRequest
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["Chat"])

@router.post("/")
async def chat(request: ChatbotRequest):
    logger.info(f"Chat request from user: {request.user_id}, thread: {request.thread_id}")
    
    config = {"configurable": {"thread_id": request.thread_id}}

    initial_state = {
        "user_id": request.user_id,
        "messages": [HumanMessage(content=request.message)]
    }
    
    return StreamingResponse(
        container.chatbot_workflow_service.run_stream(initial_state, config), 
        media_type="text/plain"
    )
