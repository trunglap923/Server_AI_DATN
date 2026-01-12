from langchain.chains.query_constructor.base import (
    AttributeInfo,
    get_query_constructor_prompt,
    load_query_constructor_runnable,
)
from langchain_elasticsearch import ElasticsearchStore
from langchain.retrievers.self_query.elasticsearch import ElasticsearchTranslator
from langchain.retrievers.self_query.base import SelfQueryRetriever
from app.core.config import settings
from app.services.core.llm_service import LLMService

class RetrievalService:
    def __init__(self, llm_service: LLMService):
        self.llm = llm_service.get_llm()
        self.embeddings = llm_service.get_embeddings()

        self.allowed_comparators = [
            "eq", "gt", "gte", "lt", "lte", "contain", "like"
        ]

        self.food_query_constructor = self._build_food_query_constructor()
        self.policy_query_constructor = self._build_policy_query_constructor()

        self.food_store = ElasticsearchStore(
            es_url=settings.ELASTIC_CLOUD_URL,
            es_api_key=settings.ELASTIC_API_KEY,
            index_name=settings.FOOD_DB_INDEX,
            embedding=self.embeddings,
        )

        self.policy_store = ElasticsearchStore(
            es_url=settings.ELASTIC_CLOUD_URL,
            es_api_key=settings.ELASTIC_API_KEY,
            index_name=settings.POLICY_DB_INDEX,
            embedding=self.embeddings,
        )

    def get_food_retriever(self, k=10):
        return SelfQueryRetriever(
            query_constructor=self.food_query_constructor,
            vectorstore=self.food_store,
            structured_query_translator=ElasticsearchTranslator(),
            search_kwargs={"k": k},
        )

    def get_policy_retriever(self, k=3):
        return SelfQueryRetriever(
            query_constructor=self.policy_query_constructor,
            vectorstore=self.policy_store,
            structured_query_translator=ElasticsearchTranslator(),
            search_kwargs={"k": k},
        )

    def _build_food_query_constructor(self):
        metadata_field_info = [
            # --- IDENTIFICATION & CLASSIFICATION ---
            AttributeInfo(name="meal_id", description="ID duy nhất của món ăn (số nguyên)", type="integer"),
            AttributeInfo(name="name", description="Tên của món ăn", type="string"),
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
            # --- INGREDIENTS ---
            AttributeInfo(name="ingredients", description="Danh sách các nguyên liệu có trong món ăn (dạng list)", type="list[string]"),
            AttributeInfo(name="ingredients_text", description="Chuỗi văn bản liệt kê toàn bộ nguyên liệu (dùng để tìm kiếm text)", type="string"),
            # --- MACROS ---
            AttributeInfo(name="kcal", description="Tổng năng lượng (kcal)", type="float"),
            AttributeInfo(name="protein", description="Hàm lượng Đạm/Protein (g)", type="float"),
            AttributeInfo(name="carbs", description="Hàm lượng Bột đường/Carbohydrate (g)", type="float"),
            AttributeInfo(name="sugar", description="Hàm lượng Đường (g)", type="float"),
            AttributeInfo(name="fiber", description="Hàm lượng Chất xơ (g)", type="float"),
            AttributeInfo(name="totalfat", description="Tổng lượng Chất béo (g)", type="float"),
            AttributeInfo(name="saturatedfat", description="Chất béo bão hòa (g)", type="float"),
            AttributeInfo(name="monounsaturatedfat", description="Chất béo không bão hòa đơn (g)", type="float"),
            AttributeInfo(name="polyunsaturatedfat", description="Chất béo không bão hòa đa (g)", type="float"),
            AttributeInfo(name="transfat", description="Chất béo chuyển hóa (g)", type="float"),
            AttributeInfo(name="cholesterol", description="Hàm lượng Cholesterol (mg)", type="float"),
            # --- VITAMINS ---
            AttributeInfo(name="vitamina", description="Vitamin A (mg)", type="float"),
            AttributeInfo(name="vitamind", description="Vitamin D (mg)", type="float"),
            AttributeInfo(name="vitaminc", description="Vitamin C (mg)", type="float"),
            AttributeInfo(name="vitaminb6", description="Vitamin B6 (mg)", type="float"),
            AttributeInfo(name="vitaminb12", description="Vitamin B12 (mg)", type="float"),
            AttributeInfo(name="vitamine", description="Vitamin E (mg)", type="float"),
            AttributeInfo(name="vitamink", description="Vitamin K (mg)", type="float"),
            AttributeInfo(name="choline", description="Choline (mg)", type="float"),
            # --- MINERALS ---
            AttributeInfo(name="canxi", description="Canxi (mg)", type="float"),
            AttributeInfo(name="fe", description="Sắt/Fe (mg)", type="float"),
            AttributeInfo(name="magie", description="Magie (mg)", type="float"),
            AttributeInfo(name="photpho", description="Phốt pho (mg)", type="float"),
            AttributeInfo(name="kali", description="Kali (mg)", type="float"),
            AttributeInfo(name="natri", description="Natri (mg)", type="float"),
            AttributeInfo(name="zn", description="Kẽm/Zn (mg)", type="float"),
            # --- OTHERS ---
            AttributeInfo(name="water", description="Hàm lượng Nước (g)", type="float"),
            AttributeInfo(name="caffeine", description="Caffeine (mg)", type="float"),
            AttributeInfo(name="alcohol", description="Cồn/Alcohol (g)", type="float"),
        ]

        document_content_description = """
        Thông tin chi tiết về các món ăn.
        Quy tắc ánh xạ Tag (Tag Mapping Rules):
        - Nếu người dùng tìm "Giàu/Nhiều X", hãy dùng tag "#HighX" (ví dụ: Giàu đạm -> #HighProtein, Giàu Sắt -> #HighFe).
        - Nếu người dùng tìm "Ít/Thấp X", hãy dùng tag "#LowX" (ví dụ: Ít béo -> #LowSaturatedFat, Ít đường -> #LowSugar).
        - Các thực phẩm cụ thể thường có tag tương ứng (Hải sản -> #HảiSản, Rau -> #RauXanh).
        """

        examples = [
            ("Gợi ý các món ăn có trứng và ít hơn 500 kcal.", {"query": "món ăn từ trứng", "filter": 'and(lt("kcal", 500), contain("ingredients", "Trứng"))'}),
            ("Tìm món ăn không chứa trứng nhưng có nhiều protein hơn 30g.", {"query": "món ăn giàu đạm", "filter": 'and(gt("protein", 30), not(contain("ingredients", "Trứng")))'}),
            ("Món ăn có cà rốt, rong biển và trên 300 kcal.", {"query": "món ăn nguyên liệu cụ thể", "filter": 'and(gt("kcal", 300), contain("ingredients", "Cà Rốt"), contain("ingredients", "Rong Biển"))'}),
            ("Món ăn giàu chất xơ, trên 10g, ít đường dưới 5g.", {"query": "món ăn healthy", "filter": 'and(gt("fiber", 10), lt("sugar", 5))'}),
            ("Món ăn có vitamin C trên 50mg và ít chất béo dưới 10g.", {"query": "món ăn giàu vitamin C", "filter": 'and(gt("vitaminc", 50), lt("totalfat", 10))'}),
            ("Gợi ý các món ăn keto với nhiều chất béo (trên 20g) nhưng ít carb (dưới 5g).", {"query": "món ăn keto", "filter": 'and(gt("totalfat", 20), lt("carbs", 5))'}),
            ("Gợi ý các món giàu đạm (nhiều protein) và ít tinh bột.", {"query": "món ăn giàu đạm ít tinh bột", "filter": 'and(contain("tags", "#HighProtein"), contain("tags", "#LowCarbs"))'}),
            ("Tìm món ăn ít calo để giảm cân.", {"query": "món ăn giảm cân", "filter": 'contain("tags", "#LowCalories")'}),
            ("Tìm món thanh đạm, ít béo bão hòa.", {"query": "món ăn thanh đạm", "filter": 'contain("tags", "#LowSaturatedFat")'}),
            ("Món ăn bổ máu (giàu sắt).", {"query": "món ăn bổ máu", "filter": 'contain("tags", "#HighFe")'}),
            ("Món ăn giàu canxi cho xương chắc khỏe.", {"query": "món ăn giàu canxi", "filter": 'contain("tags", "#HighCanxi")'}),
            ("Món ăn tốt cho mắt (giàu vitamin A).", {"query": "món ăn tốt cho mắt", "filter": 'contain("tags", "#HighVitaminA")'}),
            ("Tìm món tốt cho tim mạch, ít cholesterol.", {"query": "món ăn tốt cho tim mạch", "filter": 'contain("tags", "#LowCholesterol")'}),
            ("Tìm món ăn nhạt muối cho người huyết áp cao.", {"query": "món ăn nhạt muối", "filter": 'contain("tags", "#LowNatri")'}),
            ("Tìm món lẩu hải sản", {"query": "lẩu hải sản", "filter": 'and(contain("tags", "#Lẩu"), contain("tags", "#HảiSản"))'}),
            ("Món chay có nhiều rau xanh.", {"query": "món chay rau xanh", "filter": 'contain("tags", "#RauXanh")'})
        ]

        return load_query_constructor_runnable(
            llm=self.llm,
            document_contents=document_content_description,
            attribute_info=metadata_field_info,
            examples=examples,
            allowed_comparators=self.allowed_comparators
        )

    def _build_policy_query_constructor(self):
        metadata_field_info = [
            AttributeInfo(
                name="doc_type",
                description=(
                    "Thể loại tài liệu của ứng dụng. Ví dụ: "
                    "'product_overview' (giới thiệu ứng dụng), "
                    "'product_features' (chức năng & cách sử dụng), "
                    "'policy_and_disclaimer' (chính sách, điều khoản, miễn trừ), "
                    "'organization_info' (thông tin đội ngũ, liên hệ)."
                ),
                type="string",
            ),
            AttributeInfo(name="source", description="Nguồn nội dung của tài liệu.", type="string"),
        ]

        document_content_description = (
            "Nội dung tài liệu mô tả ứng dụng gợi ý món ăn và dinh dưỡng, "
            "bao gồm giới thiệu ứng dụng, chức năng, chính sách sử dụng, "
            "tuyên bố miễn trừ trách nhiệm, thông tin đội ngũ phát triển "
            "và các câu hỏi thường gặp."
        )

        examples = [
            ("Ứng dụng này dùng để làm gì?", {"query": "giới thiệu và mục đích của ứng dụng gợi ý món ăn", "filter": 'eq("doc_type", "product_overview")'}),
            ("App này dành cho đối tượng nào?", {"query": "đối tượng sử dụng và phạm vi ứng dụng", "filter": 'eq("doc_type", "product_overview")'}),
            ("Ứng dụng có những chức năng gì?", {"query": "các chức năng chính của ứng dụng", "filter": 'eq("doc_type", "product_features")'}),
            ("Chatbot AI trong app dùng như thế nào?", {"query": "cách sử dụng chatbot AI trong ứng dụng", "filter": 'eq("doc_type", "product_features")'}),
            ("Ứng dụng có bảo mật dữ liệu cá nhân không?", {"query": "chính sách quyền riêng tư và bảo mật dữ liệu", "filter": 'eq("doc_type", "policy_and_disclaimer")'}),
            ("Chatbot có thay thế chuyên gia dinh dưỡng không?", {"query": "tuyên bố miễn trừ trách nhiệm về AI và dinh dưỡng", "filter": 'eq("doc_type", "policy_and_disclaimer")'}),
            ("Thông tin trong app có đáng tin không?", {"query": "giới hạn trách nhiệm và phạm vi sử dụng thông tin", "filter": 'eq("doc_type", "policy_and_disclaimer")'}),
            ("Ai là người phát triển ứng dụng này?", {"query": "thông tin người sáng lập và đội ngũ phát triển", "filter": 'eq("doc_type", "organization_info")'}),
            ("Tôi cần liên hệ hỗ trợ ở đâu?", {"query": "thông tin liên hệ và hỗ trợ người dùng", "filter": 'eq("doc_type", "organization_info")'}),
            ("Ứng dụng này có uy tín không?", {"query": "giới thiệu đội ngũ phát triển và mục tiêu ứng dụng", "filter": 'eq("doc_type", "organization_info")'}),
        ]

        return load_query_constructor_runnable(
            llm=self.llm,
            document_contents=document_content_description,
            attribute_info=metadata_field_info,
            examples=examples,
            allowed_comparators=self.allowed_comparators
        )
