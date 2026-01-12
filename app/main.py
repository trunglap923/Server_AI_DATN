from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.controllers.meal_controller import router as meal_router
from app.controllers.chatbot_controller import router as chatbot_router
from app.controllers.food_similarity_controller import router as food_similarity_router
from app.controllers.food_management_controller import router as food_management_router
from app.core.config import settings

app = FastAPI(
    title="AI Meal Chatbot API",
    description="Clean Architecture implementation of Meal Recommendation System",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(meal_router)
app.include_router(chatbot_router)
app.include_router(food_similarity_router)
app.include_router(food_management_router)

@app.get("/")
def root():
    return {"message": "AI Meal Chatbot API is running 🚀"}

# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
