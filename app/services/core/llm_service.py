from langchain_deepseek import ChatDeepSeek
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler
from langchain_community.embeddings import HuggingFaceEmbeddings
from app.core.config import settings

class LLMService:
    def __init__(self):
        if not settings.DEEPSEEK_API_KEY:
             raise ValueError("❌ Missing Environment Variable: DEEPSEEK_API_KEY")
        self._llm = ChatDeepSeek(
            model="deepseek-chat",
            temperature=0.3,
            max_tokens=2048,
            timeout=30,
            max_retries=2,
            api_key=settings.DEEPSEEK_API_KEY
        )
        self._embeddings = self._init_embeddings()

    def _init_embeddings(self):
        model_name = "Alibaba-NLP/gte-multilingual-base"
        return HuggingFaceEmbeddings(
            model_name=model_name,
            model_kwargs={"trust_remote_code": True}
        )

    def get_llm(self):
        return self._llm

    def get_embeddings(self):
        return self._embeddings
