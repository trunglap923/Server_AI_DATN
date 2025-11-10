from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from langchain_core.messages import HumanMessage
from chatbot.agents.states.state import AgentState
from chatbot.agents.graphs.chatbot_graph import workflow_chatbot

# --- Định nghĩa request body ---
class ChatRequest(BaseModel):
    user_id: str
    message: str

# --- Tạo router ---
router = APIRouter(
    prefix="/chat",
    tags=["Chatbot"]
)

# --- Route xử lý chat ---
@router.post("/")
def chat(request: ChatRequest):
    try:
        
        print("Nhận được yêu cầu chat từ user:", request.user_id)
        
        # 1. Tạo state mới
        state = AgentState()
        state["user_id"] = request.user_id
        state["messages"] = request.message or [HumanMessage(content="Tập luyện sức khỏe như nào cho tốt?")]

        # 2. Lấy workflow chatbot
        graph = workflow_chatbot()

        # 3. Invoke workflow
        result = graph.invoke(state)

        # 4. Trả response
        response = result["response"] or "Không có kết quả"
        return {"response": response}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi chatbot: {e}")
