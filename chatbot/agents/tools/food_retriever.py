# ========================================
# 🥗 FOOD RETRIEVER - ElasticSearch Retriever
# ========================================

import os
from langchain.chains.query_constructor.base import (
    AttributeInfo,
    get_query_constructor_prompt,
    StructuredQueryOutputParser,
)
from langchain_deepseek import ChatDeepSeek
from langchain_elasticsearch import ElasticsearchStore
from langchain.retrievers.self_query.elasticsearch import ElasticsearchTranslator
from langchain.retrievers.self_query.base import SelfQueryRetriever

from chatbot.models.embeddings import embeddings  # Import embeddings đã khởi tạo sẵn
from chatbot.models.llm_setup import llm
from chatbot.config import ELASTIC_CLOUD_URL, ELASTIC_API_KEY


# ========================================
# 1️⃣ Định nghĩa metadata field info
# ========================================
metadata_field_info = [

    # Thông tin chung về món ăn
    AttributeInfo(
        name="meal_id",
        description="ID duy nhất của món ăn",
        type="integer"
    ),
    AttributeInfo(
        name="name",
        description="Tên món ăn",
        type="string"
    ),
    AttributeInfo(
        name="servings",
        description="Số khẩu phần ăn",
        type="integer"
    ),
    AttributeInfo(
        name="difficulty",
        description="Độ khó chế biến",
        type="string"
    ),
    AttributeInfo(
        name="cooking_time_minutes",
        description="Thời gian nấu (phút)",
        type="integer"
    ),

     # Nguyên liệu
    AttributeInfo(
        name="ingredients",
        description="Danh sách nguyên liệu (list string), ví dụ: ['cà rốt', 'rong biển', 'trứng gà']",
        type="string"
    ),
    AttributeInfo(
        name="ingredients_text",
        description="Nguyên liệu ở dạng chuỗi nối, ví dụ: 'cà rốt, rong biển, trứng gà'",
        type="string"
    ),

    # Năng lượng & chất đa lượng
    AttributeInfo(
        name="kcal",
        description="Năng lượng của món ăn (kcal)",
        type="float"
    ),
    AttributeInfo(
        name="protein",
        description="Hàm lượng protein (g)",
        type="float"
    ),
    AttributeInfo(
        name="carbohydrate",
        description="Hàm lượng carbohydrate (g)",
        type="float"
    ),
    AttributeInfo(
        name="sugar",
        description="Hàm lượng đường tổng (g)",
        type="float"
    ),
    AttributeInfo(
        name="fiber",
        description="Hàm lượng chất xơ (g)",
        type="float"
    ),
    AttributeInfo(
        name="lipid",
        description="Tổng chất béo (g)",
        type="float"
    ),
    AttributeInfo(
        name="saturated_fat",
        description="Chất béo bão hòa (g)",
        type="float"
    ),
    AttributeInfo(
        name="monounsaturated_fat",
        description="Chất béo không bão hòa đơn (g)",
        type="float"
    ),
    AttributeInfo(
        name="polyunsaturated_fat",
        description="Chất béo không bão hòa đa (g)",
        type="float"
    ),
    AttributeInfo(
        name="trans_fat",
        description="Chất béo chuyển hóa (g)",
        type="float"
    ),
    AttributeInfo(
        name="cholesterol",
        description="Hàm lượng cholesterol (mg)",
        type="float"
    ),

    # Vitamin
    AttributeInfo(
        name="vit_a",
        description="Vitamin A (mg)",
        type="float"
    ),
    AttributeInfo(
        name="vit_d",
        description="Vitamin D (mg)",
        type="float"
    ),
    AttributeInfo(
        name="vit_c",
        description="Vitamin C (mg)",
        type="float"
    ),
    AttributeInfo(
        name="vit_b6",
        description="Vitamin B6 (mg)",
        type="float"
    ),
    AttributeInfo(
        name="vit_b12",
        description="Vitamin B12 (mg)",
        type="float"
    ),
    AttributeInfo(
        name="vit_b12_added",
        description="Vitamin B12 bổ sung (mg)",
        type="float"
    ),
    AttributeInfo(
        name="vit_e",
        description="Vitamin E (mg)",
        type="float"
    ),
    AttributeInfo(
        name="vit_e_added",
        description="Vitamin E bổ sung (mg)",
        type="float"
    ),
    AttributeInfo(
        name="vit_k",
        description="Vitamin K (mg)",
        type="float"
    ),
    AttributeInfo(
        name="choline",
        description="Choline (mg)",
        type="float"
    ),

    # Khoáng chất
    AttributeInfo(
        name="canxi",
        description="Canxi (mg)",
        type="float"
    ),
    AttributeInfo(
        name="sat",
        description="Sắt (mg)",
        type="float"
    ),
    AttributeInfo(
        name="magie",
        description="Magie (mg)",
        type="float"
    ),
    AttributeInfo(
        name="photpho",
        description="Phốt pho (mg)",
        type="float"
    ),
    AttributeInfo(
        name="kali",
        description="Kali (mg)",
        type="float"
    ),
    AttributeInfo(
        name="natri",
        description="Natri (mg)",
        type="float"
    ),
    AttributeInfo(
        name="kem",
        description="Kẽm (mg)",
        type="float"
    ),

    # Thành phần khác
    AttributeInfo(
        name="water",
        description="Hàm lượng nước (g)",
        type="float"
    ),
    AttributeInfo(
        name="caffeine",
        description="Caffeine (mg)",
        type="float"
    ),
    AttributeInfo(
        name="alcohol",
        description="Cồn (g)",
        type="float"
    ),
]

document_content_description = "Mô tả ngắn gọn về món ăn"


# ========================================
# 2️⃣ Định nghĩa toán tử hỗ trợ và ví dụ
# ========================================
allowed_comparators = [
    "$eq",
    "$gt",
    "$gte",
    "$lt",
    "$lte",
    "$contain",
    "$like",
]

examples = [
    (
        "Gợi ý các món ăn có trứng và ít hơn 500 kcal.",
        {
            "query": "món ăn có trứng",
            "filter": 'and(lt("kcal", 500), contain("ingredients", "trứng"))',
        },
    ),
    (
        "Tìm món ăn không chứa trứng nhưng có nhiều protein hơn 30g.",
        {
            "query": "món ăn không có trứng",
            "filter": 'and(gt("protein", 30), not(contain("ingredients", "trứng")))',
        },
    ),
    (
        "Món ăn chay dễ nấu trong vòng 20 phút.",
        {
            "query": "món ăn chay",
            "filter": 'and(lte("cooking_time_minutes", 20), eq("difficulty", "easy"), not(contain("ingredients", "thịt")), not(contain("ingredients", "cá")))',
        },
    ),
    (
        "Món ăn giàu chất xơ, trên 10g, ít đường dưới 5g.",
        {
            "query": "món ăn giàu chất xơ",
            "filter": 'and(gt("fiber", 10), lt("sugar", 5))',
        },
    ),
    (
        "Món ăn có vitamin C trên 50mg và ít chất béo dưới 10g.",
        {
            "query": "món ăn nhiều vitamin C",
            "filter": 'and(gt("vit_c", 50), lt("lipid", 10))',
        },
    ),
    (
        "Gợi ý các món ăn keto với nhiều chất béo nhưng ít carb.",
        {
            "query": "món ăn keto",
            "filter": 'and(gt("lipid", 20), lt("carbohydrate", 5))',
        },
    ),
    (
        "Món ăn có cà rốt, rong biển và trên 300 kcal.",
        {
            "query": "món ăn có cà rốt và rong biển",
            "filter": 'and(gt("kcal", 300), contain("ingredients", "cà rốt"), contain("ingredients", "rong biển"))',
        },
    ),
    (
        "Tìm món có khoảng 500 kcal và 20g protein",
        {
            "query": "món ăn có năng lượng trung bình",
            "filter": 'and(gte("kcal", 450), lte("kcal", 450), gte("protein", 15), lte("protein", 25))',
        },
    )
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
    max_retries=2,
)

output_parser = StructuredQueryOutputParser.from_components()
query_constructor = prompt_query | llm | output_parser


# ========================================
# 4️⃣ Kết nối Elasticsearch
# ========================================
docsearch = ElasticsearchStore(
    es_url=ELASTIC_CLOUD_URL,
    es_api_key=ELASTIC_API_KEY,
    index_name="food_vdb",
    embedding=embeddings,
)


# ========================================
# 5️⃣ Tạo retrievers (nhiều cấu hình)
# ========================================

# Truy vấn rộng hơn, trả về nhiều kết quả để lọc sau
food_retriever = SelfQueryRetriever(
    query_constructor=query_constructor,
    vectorstore=docsearch,
    structured_query_translator=ElasticsearchTranslator(),
    search_kwargs={"k": 20},
)

# Truy vấn ngắn gọn hơn, trả về top-3 kết quả
food_retriever_top3 = SelfQueryRetriever(
    query_constructor=query_constructor,
    vectorstore=docsearch,
    structured_query_translator=ElasticsearchTranslator(),
    search_kwargs={"k": 3},
)


# ========================================
# 6️⃣ EXPORT
# ========================================
__all__ = ["food_retriever", "food_retriever_top3", "docsearch", "query_constructor"]
