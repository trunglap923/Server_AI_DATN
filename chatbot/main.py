from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from chatbot.routes.chat_router import router as chat_router

app = FastAPI(
    title="AI Meal Chatbot API",
    description="API gợi ý món ăn, thực đơn, và tư vấn dinh dưỡng bằng AI",
    version="1.0.0",
)

# Cho phép CORS để kết nối frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # ⚠️ đổi sau nếu cần bảo mật
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Đăng ký route
app.include_router(chat_router)

@app.get("/")
def root():
    return {"message": "AI Meal Chatbot API is running 🚀"}
