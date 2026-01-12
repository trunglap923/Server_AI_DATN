import logging
from langchain_core.documents import Document
from app.services.core.retrieval_service import RetrievalService
from app.schema.food_payload import FoodItemPayload

logger = logging.getLogger(__name__)

class FoodManagementService:
    def __init__(self, retrieval_service: RetrievalService):
        self.retrieval_service = retrieval_service
        self.food_store = retrieval_service.food_store

    def save_food(self, item: FoodItemPayload) -> bool:
        try:
            page_content = item.text_for_embedding
            metadata = item.metadata
            # Ensure ID is string
            doc_id = str(metadata.get("meal_id", ""))
            
            if not doc_id:
                raise ValueError("Metadata must contain 'meal_id'")

            doc = Document(
                page_content=page_content,
                metadata=metadata
            )
            
            # ElasticsearchStore.add_documents handles embedding generation automatically
            self.food_store.add_documents(documents=[doc], ids=[doc_id])
            
            logger.info(f"✅ Saved food with ID: {doc_id}")
            return True
        except Exception as e:
            logger.error(f"❌ Error saving food: {e}")
            raise e

    def delete_food(self, meal_id: str) -> bool:
        try:
            self.food_store.delete(ids=[meal_id])
            logger.info(f"✅ Deleted food with ID: {meal_id}")
            return True
        except Exception as e:
            logger.error(f"❌ Error deleting food: {e}")
            raise e
