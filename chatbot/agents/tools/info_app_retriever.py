from langchain.chains.query_constructor.base import (
    AttributeInfo,
    get_query_constructor_prompt,
    StructuredQueryOutputParser,
)
from langchain_deepseek import ChatDeepSeek
from langchain_elasticsearch import ElasticsearchStore
from langchain.retrievers.self_query.elasticsearch import ElasticsearchTranslator
from langchain.chains.query_constructor.base import load_query_constructor_runnable
from langchain.retrievers.self_query.base import SelfQueryRetriever

from chatbot.models.embeddings import embeddings
from chatbot.models.llm_setup import llm
from chatbot.config import ELASTIC_CLOUD_URL, ELASTIC_API_KEY, POLICY_DB_INDEX

# ========================================
# 1️⃣ Định nghĩa metadata field info
# ========================================
metadata_field_info = [
    AttributeInfo(
        name="doc_type",
        description=(
            "Thể loại tài liệu của ứng dụng. "
            "Ví dụ: "
            "'product_overview' (giới thiệu ứng dụng), "
            "'product_features' (chức năng & cách sử dụng), "
            "'policy_and_disclaimer' (chính sách, điều khoản, miễn trừ), "
            "'organization_info' (thông tin đội ngũ, liên hệ)."
        ),
        type="string",
    ),
    AttributeInfo(
        name="source",
        description=(
            "Nguồn nội dung của tài liệu."
        ),
        type="string",
    ),
]

document_content_description = (
    "Nội dung tài liệu mô tả ứng dụng gợi ý món ăn và dinh dưỡng, "
    "bao gồm giới thiệu ứng dụng, chức năng, chính sách sử dụng, "
    "tuyên bố miễn trừ trách nhiệm, thông tin đội ngũ phát triển "
    "và các câu hỏi thường gặp."
)

# ========================================
# 2️⃣ Định nghĩa toán tử hỗ trợ và ví dụ
# ========================================
allowed_comparators = [
    "eq",      # Equal
    "gt",      # Greater than
    "gte",     # Greater than or equal
    "lt",      # Less than
    "lte",     # Less than or equal
    "contain", # Chứa (dùng cho list)
    "like"     # Giống (dùng cho string pattern)
]

examples = [

    # --- NHÓM 1: GIỚI THIỆU ỨNG DỤNG ---
    (
        "Ứng dụng này dùng để làm gì?",
        {
            "query": "giới thiệu và mục đích của ứng dụng gợi ý món ăn",
            "filter": 'eq("doc_type", "product_overview")',
        },
    ),
    (
        "App này dành cho đối tượng nào?",
        {
            "query": "đối tượng sử dụng và phạm vi ứng dụng",
            "filter": 'eq("doc_type", "product_overview")',
        },
    ),

    # --- NHÓM 2: CHỨC NĂNG & CÁCH SỬ DỤNG ---
    (
        "Ứng dụng có những chức năng gì?",
        {
            "query": "các chức năng chính của ứng dụng",
            "filter": 'eq("doc_type", "product_features")',
        },
    ),
    (
        "Chatbot AI trong app dùng như thế nào?",
        {
            "query": "cách sử dụng chatbot AI trong ứng dụng",
            "filter": 'eq("doc_type", "product_features")',
        },
    ),

    # --- NHÓM 3: CHÍNH SÁCH & AN TOÀN ---
    (
        "Ứng dụng có bảo mật dữ liệu cá nhân không?",
        {
            "query": "chính sách quyền riêng tư và bảo mật dữ liệu",
            "filter": 'eq("doc_type", "policy_and_disclaimer")',
        },
    ),
    (
        "Chatbot có thay thế chuyên gia dinh dưỡng không?",
        {
            "query": "tuyên bố miễn trừ trách nhiệm về AI và dinh dưỡng",
            "filter": 'eq("doc_type", "policy_and_disclaimer")',
        },
    ),
    (
        "Thông tin trong app có đáng tin không?",
        {
            "query": "giới hạn trách nhiệm và phạm vi sử dụng thông tin",
            "filter": 'eq("doc_type", "policy_and_disclaimer")',
        },
    ),

    # --- NHÓM 4: ĐỘI NGŨ & LIÊN HỆ ---
    (
        "Ai là người phát triển ứng dụng này?",
        {
            "query": "thông tin người sáng lập và đội ngũ phát triển",
            "filter": 'eq("doc_type", "organization_info")',
        },
    ),
    (
        "Tôi cần liên hệ hỗ trợ ở đâu?",
        {
            "query": "thông tin liên hệ và hỗ trợ người dùng",
            "filter": 'eq("doc_type", "organization_info")',
        },
    ),
    (
        "Ứng dụng này có uy tín không?",
        {
            "query": "giới thiệu đội ngũ phát triển và mục tiêu ứng dụng",
            "filter": 'eq("doc_type", "organization_info")',
        },
    ),

]

# ========================================
# 3️⃣ Tạo Query Constructor
# ========================================
prompt_query = get_query_constructor_prompt(
    document_content_description,
    metadata_field_info,
    allowed_comparators=allowed_comparators,
    examples=examples,
)

llm = ChatDeepSeek(
    model="deepseek-chat",
    temperature=0,
    max_tokens=None,
    timeout=None,
    max_retries=2
)

query_constructor = load_query_constructor_runnable(
    llm=llm,
    document_contents=document_content_description,
    attribute_info=metadata_field_info,
    examples=examples,
    allowed_comparators=allowed_comparators
)

# ========================================
# 4️⃣ Kết nối Elasticsearch
# ========================================
policy_search = ElasticsearchStore(
    es_url=ELASTIC_CLOUD_URL,
    es_api_key=ELASTIC_API_KEY,
    index_name=POLICY_DB_INDEX,
    embedding=embeddings,
)

# ========================================
# 5️⃣ Tạo retrievers
# ========================================

policy_retriever = SelfQueryRetriever(
    query_constructor=query_constructor,
    vectorstore=policy_search,
    structured_query_translator=ElasticsearchTranslator(),
    search_kwargs={"k": 3},
)

__all__ = ["policy_retriever", "policy_search"]