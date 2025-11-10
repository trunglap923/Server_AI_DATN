"""
models/llm_setup.py
-------------------
Khởi tạo LLM DeepSeek cho toàn bộ hệ thống.
"""

from langchain_deepseek import ChatDeepSeek
from chatbot.config import DEEPSEEK_API_KEY

# ========================================
# 1️⃣ KIỂM TRA CẤU HÌNH
# ========================================
if not DEEPSEEK_API_KEY:
    raise ValueError("❌ Thiếu biến môi trường: DEEPSEEK_API_KEY trong file .env")

# ========================================
# 2️⃣ KHỞI TẠO LLM CHÍNH
# ========================================
llm = ChatDeepSeek(
    model="deepseek-chat",
    temperature=0.3,
    max_tokens=2048,
    timeout=30,
    max_retries=2,
)

# ========================================
# 3️⃣ TIỆN ÍCH KHỞI TẠO LLM KHÁC
# ========================================
def get_llm(model_name: str = "deepseek-chat", temperature: float = 0.3):
    """
    Khởi tạo model LLM khác (ví dụ deepseek-coder).
    """
    return ChatDeepSeek(
        model=model_name,
        temperature=temperature,
        max_tokens=2048,
        timeout=30,
        max_retries=2,
    )

# ========================================
# 4️⃣ EXPORT
# ========================================
__all__ = ["llm", "get_llm"]
