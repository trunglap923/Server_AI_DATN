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
from chatbot.config import ELASTIC_CLOUD_URL, ELASTIC_API_KEY, FOOD_DB_INDEX


# ========================================
# 1️⃣ Định nghĩa metadata field info
# ========================================
metadata_field_info = [
    # --- THÔNG TIN ĐỊNH DANH & PHÂN LOẠI ---
    AttributeInfo(
        name="meal_id",
        description="ID duy nhất của món ăn (số nguyên)",
        type="integer"
    ),
    AttributeInfo(
        name="name",
        description="Tên của món ăn",
        type="string"
    ),
    AttributeInfo(
        name="tags",
        description=(
            "Danh sách các thẻ phân loại đặc điểm món ăn. Bao gồm các nhóm chính: "
            "1. Nhóm thực phẩm: #HảiSản, #Thịt, #RauXanh, #Lẩu, #ĐồĂnNhanh... "
            "2. Dinh dưỡng (Macros): #HighProtein (Giàu đạm), #LowCarbs (Ít tinh bột), #LowCalories (Ít calo)... "
            "3. Chất béo: #LowSaturatedFat (Ít béo bão hòa), #LowCholesterol... "
            "4. Vitamin & Khoáng chất: #HighVitaminC, #HighFe (Giàu Sắt), #HighCanxi... "
            "Lưu ý: Các tag thường bắt đầu bằng dấu # và viết liền (PascalCase)."
        ),
        type="list[string]"
    ),

    # --- NGUYÊN LIỆU ---
    AttributeInfo(
        name="ingredients",
        description="Danh sách các nguyên liệu có trong món ăn (dạng list)",
        type="list[string]"
    ),
    AttributeInfo(
        name="ingredients_text",
        description="Chuỗi văn bản liệt kê toàn bộ nguyên liệu (dùng để tìm kiếm text)",
        type="string"
    ),

    # --- NĂNG LƯỢNG & MACROS (CHẤT ĐA LƯỢNG) ---
    AttributeInfo(
        name="kcal",
        description="Tổng năng lượng (kcal)",
        type="float"
    ),
    AttributeInfo(
        name="protein",
        description="Hàm lượng Đạm/Protein (g)",
        type="float"
    ),
    AttributeInfo(
        name="carbs",
        description="Hàm lượng Bột đường/Carbohydrate (g)",
        type="float"
    ),
    AttributeInfo(
        name="sugar",
        description="Hàm lượng Đường (g)",
        type="float"
    ),
    AttributeInfo(
        name="fiber",
        description="Hàm lượng Chất xơ (g)",
        type="float"
    ),
    # --- CẬP NHẬT MỚI: TOTAL FAT ---
    AttributeInfo(
        name="totalfat",
        description="Tổng lượng Chất béo (g)",
        type="float"
    ),
    AttributeInfo(
        name="saturatedfat",
        description="Chất béo bão hòa (g)",
        type="float"
    ),
    AttributeInfo(
        name="monounsaturatedfat",
        description="Chất béo không bão hòa đơn (g)",
        type="float"
    ),
    AttributeInfo(
        name="polyunsaturatedfat",
        description="Chất béo không bão hòa đa (g)",
        type="float"
    ),
    AttributeInfo(
        name="transfat",
        description="Chất béo chuyển hóa (g)",
        type="float"
    ),
    AttributeInfo(
        name="cholesterol",
        description="Hàm lượng Cholesterol (mg)",
        type="float"
    ),

    # --- VITAMINS ---
    AttributeInfo(
        name="vitamina",
        description="Vitamin A (mg)",
        type="float"
    ),
    AttributeInfo(
        name="vitamind",
        description="Vitamin D (mg)",
        type="float"
    ),
    AttributeInfo(
        name="vitaminc",
        description="Vitamin C (mg)",
        type="float"
    ),
    AttributeInfo(
        name="vitaminb6",
        description="Vitamin B6 (mg)",
        type="float"
    ),
    AttributeInfo(
        name="vitaminb12",
        description="Vitamin B12 (mg)",
        type="float"
    ),
    AttributeInfo(
        name="vitamine",
        description="Vitamin E (mg)",
        type="float"
    ),
    AttributeInfo(
        name="vitamink",
        description="Vitamin K (mg)",
        type="float"
    ),
    AttributeInfo(
        name="choline",
        description="Choline (mg)",
        type="float"
    ),

    # --- KHOÁNG CHẤT ---
    AttributeInfo(
        name="canxi",
        description="Canxi (mg)",
        type="float"
    ),
    AttributeInfo(
        name="fe",
        description="Sắt/Fe (mg)",
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
        name="zn",
        description="Kẽm/Zn (mg)",
        type="float"
    ),

    # --- THÀNH PHẦN KHÁC ---
    AttributeInfo(
        name="water",
        description="Hàm lượng Nước (g)",
        type="float"
    ),
    AttributeInfo(
        name="caffeine",
        description="Caffeine (mg)",
        type="float"
    ),
    AttributeInfo(
        name="alcohol",
        description="Cồn/Alcohol (g)",
        type="float"
    ),
]

document_content_description = """
Thông tin chi tiết về các món ăn.
Quy tắc ánh xạ Tag (Tag Mapping Rules):
- Nếu người dùng tìm "Giàu/Nhiều X", hãy dùng tag "#HighX" (ví dụ: Giàu đạm -> #HighProtein, Giàu Sắt -> #HighFe).
- Nếu người dùng tìm "Ít/Thấp X", hãy dùng tag "#LowX" (ví dụ: Ít béo -> #LowSaturatedFat, Ít đường -> #LowSugar).
- Các thực phẩm cụ thể thường có tag tương ứng (Hải sản -> #HảiSản, Rau -> #RauXanh).
"""

# ========================================
# 2️⃣ Định nghĩa toán tử hỗ trợ và ví dụ
# ========================================
allowed_comparators = [
    "eq",
    "gt",
    "gte",
    "lt",
    "lte",
    "contain",
    "like"
]

examples = [
    # --- NHÓM 1: NGUYÊN LIỆU & SỐ LIỆU CỤ THỂ (Ưu tiên logic số học) ---
    (
        "Gợi ý các món ăn có trứng và ít hơn 500 kcal.",
        {
            "query": "món ăn từ trứng",
            # Dùng contain cho ingredients, lt cho kcal
            "filter": 'and(lt("kcal", 500), contain("ingredients", "Trứng"))',
        },
    ),
    (
        "Tìm món ăn không chứa trứng nhưng có nhiều protein hơn 30g.",
        {
            "query": "món ăn giàu đạm",
            # Dùng not(contain(...))
            "filter": 'and(gt("protein", 30), not(contain("ingredients", "Trứng")))',
        },
    ),
    (
        "Món ăn có cà rốt, rong biển và trên 300 kcal.",
        {
            "query": "món ăn nguyên liệu cụ thể",
            # Contain riêng biệt cho từng nguyên liệu
            "filter": 'and(gt("kcal", 300), contain("ingredients", "Cà Rốt"), contain("ingredients", "Rong Biển"))',
        },
    ),

    # --- NHÓM 2: MACROS VỚI SỐ LIỆU (Chú ý tên trường: totalfat, carbs, vitaminc) ---
    (
        "Món ăn giàu chất xơ, trên 10g, ít đường dưới 5g.",
        {
            "query": "món ăn healthy",
            "filter": 'and(gt("fiber", 10), lt("sugar", 5))',
        },
    ),
    (
        "Món ăn có vitamin C trên 50mg và ít chất béo dưới 10g.",
        {
            "query": "món ăn giàu vitamin C",
            # Sửa map: vit_c -> vitaminc, lipid -> totalfat
            "filter": 'and(gt("vitaminc", 50), lt("totalfat", 10))',
        },
    ),
    (
        "Gợi ý các món ăn keto với nhiều chất béo (trên 20g) nhưng ít carb (dưới 5g).",
        {
            "query": "món ăn keto",
            # Sửa map: carbohydrate -> carbs
            "filter": 'and(gt("totalfat", 20), lt("carbs", 5))',
        },
    ),

    # --- NHÓM 3: MAPPING TAG TRỪU TƯỢNG (Khi không có số liệu) ---
    (
        "Gợi ý các món giàu đạm (nhiều protein) và ít tinh bột.",
        {
            "query": "món ăn giàu đạm ít tinh bột",
            # Không có số -> Dùng Tags #HighProtein, #LowCarbs
            "filter": 'and(contain("tags", "#HighProtein"), contain("tags", "#LowCarbs"))',
        },
    ),
    (
        "Tìm món ăn ít calo để giảm cân.",
        {
            "query": "món ăn giảm cân",
            # Giảm cân -> #LowCalories
            "filter": 'contain("tags", "#LowCalories")',
        },
    ),
    (
        "Tìm món thanh đạm, ít béo bão hòa.",
        {
            "query": "món ăn thanh đạm",
            # Ít béo bão hòa -> #LowSaturatedFat
            "filter": 'contain("tags", "#LowSaturatedFat")',
        },
    ),

    # --- NHÓM 4: MAPPING VITAMIN & KHOÁNG CHẤT (Fe, Zn, Canxi...) ---
    (
        "Món ăn bổ máu (giàu sắt).",
        {
            "query": "món ăn bổ máu",
            # Sắt -> #HighFe
            "filter": 'contain("tags", "#HighFe")',
        },
    ),
    (
        "Món ăn giàu canxi cho xương chắc khỏe.",
        {
            "query": "món ăn giàu canxi",
            # Canxi -> #HighCanxi
            "filter": 'contain("tags", "#HighCanxi")',
        },
    ),
    (
        "Món ăn tốt cho mắt (giàu vitamin A).",
        {
            "query": "món ăn tốt cho mắt",
            # Vitamin A -> #HighVitaminA
            "filter": 'contain("tags", "#HighVitaminA")',
        },
    ),

    # --- NHÓM 5: SỨC KHỎE TIM MẠCH & BỆNH LÝ ---
    (
        "Tìm món tốt cho tim mạch, ít cholesterol.",
        {
            "query": "món ăn tốt cho tim mạch",
            # Cholesterol -> #LowCholesterol
            "filter": 'contain("tags", "#LowCholesterol")',
        },
    ),
    (
        "Tìm món ăn nhạt muối cho người huyết áp cao.",
        {
            "query": "món ăn nhạt muối",
            # Nhạt muối/Ít Natri -> #LowNatri
            "filter": 'contain("tags", "#LowNatri")',
        },
    ),

    # --- NHÓM 6: LOẠI MÓN ĂN & NHÓM THỰC PHẨM ---
    (
        "Tìm món lẩu hải sản",
        {
            "query": "lẩu hải sản",
            # Tags loại món
            "filter": 'and(contain("tags", "#Lẩu"), contain("tags", "#HảiSản"))',
        },
    ),
    (
        "Món chay có nhiều rau xanh.",
        {
            "query": "món chay rau xanh",
            # Rau xanh -> #RauXanh
            "filter": 'contain("tags", "#RauXanh")',
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
docsearch = ElasticsearchStore(
    es_url=ELASTIC_CLOUD_URL,
    es_api_key=ELASTIC_API_KEY,
    index_name=FOOD_DB_INDEX,
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
food_retriever_3 = SelfQueryRetriever(
    query_constructor=query_constructor,
    vectorstore=docsearch,
    structured_query_translator=ElasticsearchTranslator(),
    search_kwargs={"k": 3},
)

food_retriever_50 = SelfQueryRetriever(
    query_constructor=query_constructor,
    vectorstore=docsearch,
    structured_query_translator=ElasticsearchTranslator(),
    search_kwargs={"k": 50},
)

# ========================================
# 6️⃣ EXPORT
# ========================================
__all__ = ["food_retriever", "food_retriever_3", "food_retriever_50", "docsearch", "query_constructor"]
