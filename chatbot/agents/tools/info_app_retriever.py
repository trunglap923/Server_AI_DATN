from langchain_elasticsearch import ElasticsearchStore

from chatbot.models.embeddings import embeddings
from chatbot.config import ELASTIC_CLOUD_URL, ELASTIC_API_KEY, POLICY_DB_INDEX

policy_search = ElasticsearchStore(
    es_url=ELASTIC_CLOUD_URL,
    es_api_key=ELASTIC_API_KEY,
    index_name=POLICY_DB_INDEX,
    embedding=embeddings,
)

policy_retriever = policy_search.as_retriever(
    search_kwargs={"k": 3}
)

__all__ = ["policy_retriever", "policy_search"]