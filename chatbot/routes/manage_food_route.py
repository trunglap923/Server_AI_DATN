from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from langchain_core.documents import Document
from langchain_elasticsearch import ElasticsearchStore
from chatbot.config import ELASTIC_CLOUD_URL, ELASTIC_API_KEY, FOOD_DB_INDEX
from chatbot.models.embeddings import embeddings
import logging

# --- Cấu hình logging ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Định nghĩa request body ---
class FoodItemPayload(BaseModel):
    text_for_embedding: str
    metadata: dict
    
# --- Tạo router ---
router = APIRouter(
    prefix="/manage-food",
    tags=["Food Management (CRUD)"]
)

try:
    es_store = ElasticsearchStore(
        es_url=ELASTIC_CLOUD_URL,
        es_api_key=ELASTIC_API_KEY,
        index_name=FOOD_DB_INDEX,
        embedding=embeddings,
    )
    logger.info("✅ Connected to Elasticsearch for Management.")
except Exception as e:
    logger.error(f"❌ Failed to connect to Elasticsearch: {e}")
    es_store = None

@router.post("/save")
def save_food(item: FoodItemPayload):
    if not es_store:
        raise HTTPException(status_code=500, detail="Elasticsearch connection failed.")
    
    try:
        page_content = item.text_for_embedding
        metadata = item.metadata
        id = metadata["meal_id"]
        
        doc = Document(
            page_content=page_content,
            metadata=metadata
        )
        
        es_store.add_documents(documents=[doc], ids=[id])
        
        logger.info(f"Saved food: {id}")
        return {"status": "success"}
    except Exception as e:
        logger.error(f"Error saving food: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/delete/{meal_id}")
def delete_food(meal_id: str):
    if not es_store:
        raise HTTPException(status_code=500, detail="Elasticsearch connection failed.")
    
    try:
        es_store.delete(ids=[meal_id])
        
        logger.info(f"Deleted food: {meal_id}")
        return {"status": "success"}
    except Exception as e:
        logger.error(f"Error deleting food: {e}")
        raise HTTPException(status_code=500, detail=str(e))