import logging
import operator
from typing import Dict, Any, AsyncGenerator, Literal, List, Optional

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnableConfig
from pydantic import BaseModel, Field

from app.schema.agent_state import AgentState
from app.services.core.llm_service import LLMService

# Knowledge & Utils
from app.helpers.chat_history import get_chat_history
from app.helpers.user_profile import get_user_by_id
from app.helpers.nutrition import get_restrictions
from app.knowledge.field_requirement import FIELD_NAMES_VN, TOPIC_REQUIREMENTS

logger = logging.getLogger(__name__)

# --- Helper Models for Nodes ---

class Topic(BaseModel):
    name: str = Field(
        description=(
            "Tên chủ đề mà người dùng đang hỏi. "
            "Các giá trị hợp lệ: 'meal_suggestion', 'food_suggestion', 'food_query', 'policy', 'general_chat'."
        )
    )

class MealIntent(BaseModel):
    meals_to_generate: List[str] = Field(
        description="Danh sách các bữa được người dùng muốn gợi ý: ['sáng', 'trưa', 'tối']."
    )

DiseaseType = Literal[
    "Khỏe mạnh", "Suy thận", "Xơ gan, Viêm gan", "Gout", "Sỏi thận", "Suy dinh dưỡng",
    "Bỏng nặng", "Thiếu máu thiếu sắt", "Bệnh tim mạch", "Tiểu đường", "Loãng xương",
    "Phụ nữ mang thai", "Viêm loét, trào ngược dạ dày", "Hội chứng ruột kích thích",
    "Viêm khớp", "Tăng huyết áp"
]

class MacroGoals(BaseModel):
    targetcalories: float = Field(..., description="Tổng calo mục tiêu (TDEE +/- goal)")
    protein: float = Field(..., description="Protein (gram)")
    totalfat: float = Field(..., description="Lipid/Fat (gram)")
    carbohydrate: float = Field(..., description="Tinh bột (gram)")
    heathStatus: DiseaseType = Field(..., description="Tình trạng sức khỏe")
    diet: str = Field(..., description="Chế độ ăn")

class ContextDecision(BaseModel):
    user_provided_info: bool = Field(description="True nếu user đề cập đến cân nặng, chiều cao, tuổi, hoặc mục tiêu ăn uống. False nếu user chỉ chào hỏi hoặc yêu cầu chung chung.")
    calculated_goals: Optional[MacroGoals] = Field(None, description="Kết quả tính toán NẾU đủ thông tin.")
    missing_info: List[str] = Field(default=[], description="Danh sách các thông tin còn thiếu để tính TDEE (VD: ['height', 'age']). Nếu đủ thì để trống.")

class ChatbotWorkflowService:
    def __init__(self, llm_service: LLMService, retrieval_service: Any, meal_service: Any):
        self.llm_service = llm_service
        self.retrieval_service = retrieval_service
        self.meal_service = meal_service
        
        # Initialize Retrievers
        self.food_retriever = self.retrieval_service.get_food_retriever(k=10)
        self.policy_retriever = self.retrieval_service.get_policy_retriever(k=3)
        
        self.checkpointer = MemorySaver()
        self.app = self.build_graph()

    def build_graph(self):
        workflow = StateGraph(AgentState)

        # Add Nodes
        workflow.add_node("classify_topic", self.classify_topic)
        workflow.add_node("load_context", self.load_context)
        workflow.add_node("ask_info", self.ask_missing_info)
        workflow.add_node("meal_identify", self.meal_identify)
        workflow.add_node("suggest_meal_node", self.suggest_meal_node)
        workflow.add_node("generate_final_response", self.generate_final_response)
        workflow.add_node("food_suggestion", self.food_suggestion)
        workflow.add_node("select_food_plan", self.select_food_plan)
        workflow.add_node("food_query", self.food_query)
        workflow.add_node("select_food", self.select_food)
        workflow.add_node("general_chat", self.general_chat)
        workflow.add_node("policy", self.policy)

        # Add Edges
        workflow.add_edge(START, "classify_topic")

        workflow.add_conditional_edges(
            "classify_topic",
            self.route_initial,
            {
                "policy": "policy",
                "food_query": "food_query",
                "general_chat": "general_chat",
                "load_context": "load_context"
            }
        )

        workflow.add_conditional_edges(
            "load_context",
            self.route_post_validation,
            {
                "ask_info": "ask_info",
                "meal_suggestion": "meal_identify",
                "food_suggestion": "food_suggestion",
                "general_chat": "general_chat" 
            }
        )

        workflow.add_edge("ask_info", END)

        workflow.add_edge("meal_identify", "suggest_meal_node")
        workflow.add_edge("suggest_meal_node", "generate_final_response")
        workflow.add_edge("generate_final_response", END)

        workflow.add_edge("food_suggestion", "select_food_plan")
        workflow.add_edge("select_food_plan", END)

        workflow.add_edge("food_query", "select_food")
        workflow.add_edge("select_food", END)

        workflow.add_edge("policy", END)
        workflow.add_edge("general_chat", END)

        return workflow.compile(checkpointer=self.checkpointer)

    async def run_stream(self, initial_state: Dict[str, Any], config: Dict[str, Any]) -> AsyncGenerator[str, None]:
        async for event in self.app.astream_events(
            initial_state, 
            config=config, 
            version="v2" 
        ):
            if event["event"] == "on_chat_model_stream":
                data = event.get("data", {})
                chunk = data.get("chunk")
                
                if chunk and hasattr(chunk, "content") and chunk.content:
                    yield chunk.content

    # --- Node Implementations ---

    async def classify_topic(self, state: AgentState):
        logger.info("---CLASSIFY TOPIC ---")
        all_messages = state["messages"]
        question = all_messages[-1].content
        
        system_msg = """
        Bạn là bộ điều hướng thông minh.
        Nhiệm vụ: Phân loại câu hỏi của người dùng vào nhóm thích hợp.

        CÁC NHÓM CHỦ ĐỀ:
        1. "meal_suggestion": Gợi ý thực đơn ăn uống các bữa.
        2. "food_suggestion": Gợi ý một món ăn cụ thể.
        3. "food_query": Hỏi thông tin dinh dưỡng một món ăn cụ thể.
        4. "policy": Khi người dùng hỏi về thông tin, đặc điểm, quy định, chính sách, hướng dẫn sử dụng MỚI mà chưa có trong lịch sử (liên quan đến app).
        5. "general_chat":
           - Chào hỏi xã giao.
           - Các câu hỏi sức khỏe chung chung.
           - QUAN TRỌNG: Các câu hỏi NỐI TIẾP (Follow-up) yêu cầu giải thích, làm rõ thông tin ĐÃ CÓ trong lịch sử hội thoại.

        NGUYÊN TẮC ƯU TIÊN:
        - Nếu câu hỏi mơ hồ, hãy kiểm tra lịch sử.
        - Nếu câu trả lời cho câu hỏi đó ĐÃ NẰM trong tin nhắn trước của AI -> Chọn "general_chat".
        - Chỉ chọn các topic chuyên biệt (policy/food...) khi cần tra cứu dữ liệu MỚI bên ngoài.
        """

        prompt = ChatPromptTemplate.from_messages([
            ("system", system_msg),
            MessagesPlaceholder(variable_name="history"),
            ("human", "{input}") 
        ])

        llm = self.llm_service.get_llm()
        classifier_llm = llm.with_structured_output(Topic)
        chain = prompt | classifier_llm

        recent_messages = get_chat_history(state["messages"], max_tokens=500)

        try:
            topic_result = await chain.ainvoke({
                "history": recent_messages,
                "input": question
            })
            topic_name = topic_result.name
        except Exception as e:
            logger.info(f"⚠️ Lỗi phân loại: {e}")
            topic_name = "general_chat"

        logger.info(f"Topic detected: {topic_name}")
        return {"topic": topic_name}

    async def load_context(self, state: AgentState):
        logger.info("---NODE: STRICT CONTEXT & CALCULATOR---")
        all_messages = state["messages"]
        question = all_messages[-1].content
        user_id = state.get("user_id", 1)

        system_prompt = """
        Bạn là Chuyên gia Dinh dưỡng AI.
        Nhiệm vụ: Phân tích hội thoại và xác định ngữ cảnh dữ liệu.

        LOGIC XỬ LÝ:
        1. Kiểm tra xem người dùng có đang cung cấp thông tin cá nhân (Cân nặng, Chiều cao, Tuổi, Giới tính, Mục tiêu) hoặc yêu cầu Calo cụ thể không?

        2. TRƯỜNG HỢP A: Người dùng KHÔNG cung cấp thông tin gì mới liên quan đến chỉ số cơ thể (chỉ hỏi "Gợi ý món ăn mặn"), cung cấp thông tin dinh dưỡng món ăn cũng vào trường hợp này (ví dụ "Gợi ý món ăn 400kcal).
           -> Trả về: user_provided_info = False. (Hệ thống sẽ tự dùng DB).

        3. TRƯỜNG HỢP B: Người dùng CÓ cung cấp thông tin (dù chỉ là 1 phần).
           -> Trả về: user_provided_info = True.
           -> Kiểm tra xem thông tin đã ĐỦ để tính TDEE chưa? (Cần đầy đủ ('weight', 'height', 'age', 'gender', 'activity', 'target_goal') hoặc ('targetcalories', 'protein', 'totalfat', 'carbohydrate'))
           -> NẾU THIẾU: Liệt kê các trường thiếu vào 'missing_info'.
           -> NẾU ĐỦ (hoặc user cho sẵn Target Kcal):
              - Hãy TÍNH TOÁN ngay lập tức 4 chỉ số: Kcal, Protein, Lipid, Carbohydrate.
              - Sử dụng công thức Mifflin-St Jeor cho BMR.
              - Phân bổ Macro theo chế độ ăn user mong muốn (hoặc mặc định 30P/30F/40C).
              - Trả về kết quả trong 'calculated_goals'.
        """

        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            MessagesPlaceholder(variable_name="history"), 
            ("human", "{input}")
        ])
        
        llm = self.llm_service.get_llm()
        context_llm = llm.with_structured_output(ContextDecision)
        chain = prompt | context_llm

        recent_messages = get_chat_history(state["messages"], max_tokens=500)
        
        try:
            decision = await chain.ainvoke({
                "history": recent_messages, 
                "input": question           
            })

            logger.info(f"   🤖 Decision: User Provided Info = {decision.user_provided_info}")
            logger.info(f"   📝 Missing Info: {decision.missing_info}")

        except Exception as e:
            logger.info(f"⚠️ Lỗi LLM Context: {e}")
            return {"missing_fields": ["system_error"]}

        final_nutrition_goals = {}
        missing_fields = []
        is_valid = False

        if not decision.user_provided_info:
            logger.info("   💾 Dùng Profile Database.")
            nutrition_goals = get_user_by_id(user_id)
            restrictions = get_restrictions(nutrition_goals["healthStatus"])
            final_nutrition_goals = {**nutrition_goals, **restrictions}
            is_valid = True

        else:
            logger.info("   🚀 Dùng Profile Tạm thời (Session).")
            if decision.missing_info:
                logger.info(f"   ⛔ Còn thiếu: {decision.missing_info}")
                missing_fields = decision.missing_info
                is_valid = False
            elif decision.calculated_goals:
                goals = decision.calculated_goals
                logger.info(f"   ✅ Đã tính xong: {goals.targetcalories} Kcal")

                nutrition_goals = {
                    "targetcalories": goals.targetcalories,
                    "protein": goals.protein,
                    "totalfat": goals.totalfat,
                    "carbohydrate": goals.carbohydrate,
                    "healthStatus": goals.heathStatus,
                    "diet": goals.diet
                }
                restrictions = get_restrictions(nutrition_goals["healthStatus"])
                final_nutrition_goals = {**nutrition_goals, **restrictions}
                is_valid = True

        return {
            "user_profile": final_nutrition_goals,
            "missing_fields": missing_fields,
            "is_valid": is_valid
        }

    async def ask_missing_info(self, state: AgentState, config: RunnableConfig):
        logger.info("---NODE: ASK MISSING INFO---")
        missing_fields = state.get("missing_fields", [])
        topic = state.get("topic", "")

        missing_vn = [FIELD_NAMES_VN.get(f, f) for f in missing_fields]
        missing_str = ", ".join(missing_vn)

        if topic == "meal_suggestion":
            system_instruction = f"""
            Bạn là Trợ lý Dinh dưỡng AI. Nhiệm vụ của bạn là yêu cầu người dùng cung cấp thông tin còn thiếu để lên thực đơn.
            
            Thông tin đang thiếu: **{missing_str}**.

            Hãy soạn một câu trả lời thân thiện, tự nhiên nhưng ngắn gọn, hướng dẫn người dùng cung cấp theo 1 trong 2 cách sau:
            1. Cung cấp thông tin cơ thể (Cân nặng, Chiều cao, Tuổi, Giới tính, Mức độ vận động) -> Để AI tự tính toán.
            2. Hoặc cung cấp mục tiêu dinh dưỡng cụ thể nếu đã biết (Kcal, Protein, Fat, Carb).
            
            Gợi ý ví dụ nhập liệu nhanh cho họ (ví dụ: "Mình 60kg, cao 1m7...").
            """
        else:
            system_instruction = f"""
            Bạn là Trợ lý AI. Người dùng đang yêu cầu một tác vụ nhưng thiếu thông tin.
            Thông tin cần bổ sung: **{missing_str}**.
            Hãy yêu cầu người dùng cung cấp các thông tin này một cách lịch sự, ngắn gọn và rõ ràng.
            """
            
        try:
            llm = self.llm_service.get_llm()
            messages = [
                SystemMessage(content=system_instruction),
                HumanMessage(content="Hãy hỏi người dùng thông tin còn thiếu.")
            ]

            response = await llm.ainvoke(messages, config=config)
            return {"messages": [response]}

        except Exception as e:
            logger.error(f"Lỗi LLM trong ask_missing_info: {e}")
            return {"messages": [AIMessage(content=f"Mình cần thêm thông tin về {missing_str} để tiếp tục.")]}

    async def meal_identify(self, state: AgentState):
        logger.info("---MEAL IDENTIFY---")
        messages = state["messages"]
        user_message = messages[-1].content if messages else state.get("question", "")
        
        llm = self.llm_service.get_llm()
        structured_llm = llm.with_structured_output(MealIntent)

        system = """
        Bạn là chuyên gia phân tích yêu cầu dinh dưỡng.
        Nhiệm vụ: Đọc câu hỏi người dùng và trích xuất danh sách các bữa ăn họ muốn gợi ý.
        Chỉ được chọn trong các giá trị: "sáng", "trưa", "tối".
        Nếu người dùng nói "cả ngày", hãy trả về ["sáng", "trưa", "tối"].
        """

        prompt = ChatPromptTemplate.from_messages([
            ("system", system),
            ("human", "{question}"),
        ])
        
        chain = prompt | structured_llm

        try:
            result = await chain.ainvoke({"question": user_message})

            if not result:
                logger.info("⚠️ Model không trả về định dạng đúng, dùng mặc định.")
                meals = ["sáng", "trưa", "tối"]
            else:
                meals = result.meals_to_generate

        except Exception as e:
            logger.info(f"⚠️ Lỗi Parse JSON: {e}")
            meals = ["sáng", "trưa", "tối"]

        logger.info("Bữa cần gợi ý: " + ", ".join(meals))

        return {
            "meals_to_generate": meals
        }

    async def suggest_meal_node(self, state: AgentState):
        logger.info("---SUGGEST MEAL NODE---")
        user_id = state.get("user_id", 1)
        user_profile = state.get("user_profile", {})
        meals_to_generate = state.get("meals_to_generate", [])
        messages = state.get("messages", [])
        
        if messages:
            question = messages[-1].content
        else:
            question = "Gợi ý thực đơn tiêu chuẩn"
            
        tool_input = {
            "user_id": user_id,
            "user_profile": user_profile,
            "question": question,
            "meals_to_generate": meals_to_generate
        }

        logger.info(f"👉 Gọi Service: MealSuggestionWorkflow")

        try:
            # result = await daily_meal_suggestion.ainvoke(tool_input)
            result = await self.meal_service.run(tool_input)
            
            return {
                "final_menu": result.get("final_menu"),
                "reason": result.get("reason"),
            }
        except Exception as e:
            logger.error(f"❌ Lỗi khi chạy tool suggest_meal: {e}")
            return {
                "final_menu": [],
                "reason": "Xin lỗi, hệ thống gặp sự cố khi tính toán thực đơn.",
                "error": str(e)
            }

    async def generate_final_response(self, state: AgentState, config: RunnableConfig):
        logger.info("---NODE: FINAL RESPONSE (FULL NUTRITION AI SUMMARY)---")
        menu = state.get("final_menu", [])
        profile = state.get("user_profile", {})

        if not menu:
            return {"messages": [AIMessage(content="Xin lỗi, tôi chưa thể tạo thực đơn lúc này.")]}

        meal_priority = {"sáng": 1, "trưa": 2, "tối": 3}
        sorted_menu = sorted(
            menu,
            key=lambda x: meal_priority.get(x.get('assigned_meal', '').lower(), 99)
        )

        actual_total = {"kcal": 0, "p": 0, "f": 0, "c": 0}
        menu_context = ""

        for dish in sorted_menu:
            k = dish.get('final_kcal', 0)
            p = dish.get('final_protein', 0)
            f = dish.get('final_totalfat', 0)
            c = dish.get('final_carbs', 0)
            
            actual_total["kcal"] += k
            actual_total["p"] += p
            actual_total["f"] += f
            actual_total["c"] += c

            scale = dish.get('portion_scale', 1.0)
            scale_text = f" (x{scale} suất)" if scale != 1.0 else ""
            
            menu_context += (
                f"- Bữa {dish.get('assigned_meal', '').upper()}: {dish['name']}{scale_text}\n"
                f"  + Năng lượng: {k} Kcal\n"
                f"  + Protein: {p}g | Lipid: {f}g | Carbs: {c}g\n\n"
            )

        target_kcal = int(profile.get('targetcalories', 0))
        target_p = int(profile.get('protein', 0))
        target_f = int(profile.get('totalfat', 0))
        target_c = int(profile.get('carbohydrate', 0))

        system_prompt = f"""
        Bạn là một Chuyên gia Dinh dưỡng AI. Hãy trình bày thực đơn và phân tích sâu về các chỉ số dinh dưỡng.

        DỮ LIỆU THỰC ĐƠN:
        {menu_context}

        TỔNG DINH DƯỠNG THỰC TẾ:
        - Tổng: {actual_total['kcal']} Kcal | {actual_total['p']}g P | {actual_total['f']}g F | {actual_total['c']}g C

        MỤC TIÊU CỦA NGƯỜI DÙNG:
        - Mục tiêu: {target_kcal} Kcal | {target_p}g P | {target_f}g F | {target_c}g C

        YÊU CẦU TRÌNH BÀY:
        1. Trình bày danh sách món ăn theo từng bữa.
        2. Nhận xét chi tiết về 3 nhóm chất (Macros):
            - Protein: Đủ để xây dựng cơ bắp chưa?
            - Lipid (Chất béo): Có nằm trong ngưỡng lành mạnh không?
            - Carbs (Bột đường): Có cung cấp đủ năng lượng cho hoạt động không?
        3. So sánh tổng thực tế với mục tiêu người dùng (Sai số bao nhiêu %).
        4. Đưa ra lời khuyên về cách phân bổ các chất này trong ngày.
        5. Tuyệt đối KHÔNG bịa đặt con số ngoài dữ liệu đã cho.
        6. Không dùng bảng để trình bày.
        7. Trả lời một cách ngắn gọn không dài dòng.
        """
        
        try:
            llm = self.llm_service.get_llm()
            response = await llm.ainvoke([
                SystemMessage(content=system_prompt),
                HumanMessage(content="Hãy phân tích thực đơn đầy đủ các chất giúp tôi.")
            ], config=config)

            return {"messages": [response]}

        except Exception as e:
            logger.info(f"Lỗi LLM: {e}")
            return {"messages": [AIMessage(content="Xin lỗi, có lỗi xảy ra.")]}

    async def food_suggestion(self, state: AgentState):
        logger.info("---FOOD QUERY SUGGESTION---")
        user_id = state.get("user_id", 1)
        messages = state["messages"]
        user_message = messages[-1].content if messages else state.get("question", "")

        user_profile = state.get("user_profile", {})
        suggested_meals = []

        prompt = f"""
        Người dùng có khẩu phần: {user_profile.get("diet", "Bình thường")}.
        Câu hỏi: "{user_message}".
        Hãy tìm các món ăn phù hợp với khẩu phần và yêu cầu này, cho phép sai lệch không quá 20%.
        """

        try:
            foods = await self.food_retriever.ainvoke(prompt)
            logger.info(f"🔍 Kết quả truy vấn: {len(foods)} món")
            for i, food in enumerate(foods):
                suggested_meals.append(food)
        except Exception as e:
            logger.error(f"Lỗi Retriever Food Suggestion: {e}")

        return {"suggested_meals": suggested_meals, "user_profile": user_profile}

    async def select_food_plan(self, state: AgentState, config: RunnableConfig):
        logger.info("---SELECT FOOD PLAN---")
        user_profile = state.get("user_profile", {})
        suggested_meals = state.get("suggested_meals", [])
        messages = state.get("messages", [])
        user_message = messages[-1].content if messages else state.get("question", "")
        
        if not suggested_meals:
            return {
                "messages": [AIMessage(content="Xin lỗi, dựa trên tiêu chí của bạn, tôi không tìm thấy món ăn nào phù hợp trong dữ liệu.")]
            }

        suggested_meals_text = "\n".join(
            f"Món {i+1}: {doc.metadata.get('name', 'Không rõ')}\n"
            f"   - Dinh dưỡng: {doc.metadata.get('kcal', '?')} kcal | "
            f"P: {doc.metadata.get('protein', '?')}g | L: {doc.metadata.get('totalfat', '?')}g | C: {doc.metadata.get('carbs', '?')}g\n"
            for i, doc in enumerate(suggested_meals)
        )

        system_prompt = f"""
        Bạn là chuyên gia dinh dưỡng AI.

        HỒ SƠ NGƯỜI DÙNG:
        - Mục tiêu: {user_profile.get('targetcalories', 'N/A')} kcal/ngày
        - Macro (P/F/C): {user_profile.get('protein', '?')}g / {user_profile.get('totalfat', '?')}g / {user_profile.get('carbohydrate', '?')}g
        - Chế độ: {user_profile.get('diet', 'Cân bằng')}

        CÂU HỎI:
        {user_message}

        DANH SÁCH ỨNG VIÊN TỪ DATABASE:
        {suggested_meals_text}

        NHIỆM VỤ:
        1. Dựa vào câu hỏi của người dùng, hãy chọn ra 2-3 món phù hợp nhất từ danh sách trên.
        2. Giải thích lý do chọn (dựa trên sự phù hợp về Calo/Macro hoặc khẩu vị).
        3. TUYỆT ĐỐI KHÔNG bịa ra món không có trong danh sách.
        """
        
        try:
            llm = self.llm_service.get_llm()
            response = await llm.ainvoke([
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_message)
            ], config=config)

            return {"messages": [response]}

        except Exception as e:
            logger.info(f"Lỗi LLM: {e}")
            return {"messages": [AIMessage(content="Xin lỗi, có lỗi xảy ra.")]}

    async def food_query(self, state: AgentState):
        logger.info("---FOOD QUERY---")
        messages = state["messages"]
        user_message = messages[-1].content
        
        try:
            # Note: food_retriever uses deepseek-chat internally via query_constructor which was imported
            results = await self.food_retriever.ainvoke(user_message)
            logger.info(f"Query Result Count: {len(results)}")
            return {"suggested_meals": results}
        except Exception as e:
             logger.error(f"Failed to query food retriever: {e}")
             return {"suggested_meals": []}

    async def select_food(self, state: AgentState, config: RunnableConfig):
        logger.info("---NODE: ANALYZE & ANSWER---")
        suggested_meals = state.get("suggested_meals", [])
        messages = state.get("messages", [])
        user_message = messages[-1].content if messages else state.get("question", "")

        if not suggested_meals:
            return {"messages": [AIMessage(content="Xin lỗi, tôi không tìm thấy món ăn nào phù hợp trong cơ sở dữ liệu.")]}

        meals_context = ""
        for i, doc in enumerate(suggested_meals):
            meta = doc.metadata
            meals_context += (
                f"--- Món {i+1} ---\n"
                f"Tên: {meta.get('name', 'Không tên')}\n"
                f"Dinh dưỡng (1 suất): {meta.get('kcal', '?')} kcal | "
                f"Đạm: {meta.get('protein', '?')}g | Béo: {meta.get('totalfat', '?')}g | Carb: {meta.get('carbs', '?')}g\n"
                f"Mô tả: {doc.page_content}\n\n"
            )

        system_prompt = f"""
        Bạn là Trợ lý Dinh dưỡng AI thông minh.

        DỮ LIỆU TÌM ĐƯỢC TỪ KHO MÓN ĂN:
        {meals_context}

        YÊU CẦU TRẢ LỜI:
        1. Dựa vào "Dữ liệu tìm được", hãy trả lời câu hỏi của người dùng một cách trực tiếp.
        2. Nếu người dùng hỏi thông tin (VD: "Phở bò bao nhiêu calo?"), hãy lấy số liệu chính xác từ dữ liệu trên để trả lời.
        3. Nếu không có dữ liệu phù hợp trong danh sách, hãy thành thật nói "Tôi không tìm thấy thông tin chính xác về món này trong hệ thống".

        Lưu ý: Chỉ sử dụng thông tin từ danh sách cung cấp, không bịa đặt số liệu.
        """
            
        try:
            llm = self.llm_service.get_llm()
            response = await llm.ainvoke([
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_message)
            ], config=config)

            return {"messages": [response]}

        except Exception as e:
            logger.info(f"Lỗi LLM: {e}")
            return {"messages": [AIMessage(content="Xin lỗi, có lỗi xảy ra.")]}

    async def general_chat(self, state: AgentState, config: RunnableConfig):
        logger.info("---GENERAL CHAT---")
        messages = state["messages"]
        question = messages[-1].content
        history = get_chat_history(state["messages"], max_tokens=1000)

        system_prompt = f"""
        Bạn là một chuyên gia dinh dưỡng và ẩm thực AI.
        Hãy trả lời các câu hỏi về:
        - món ăn, thành phần, dinh dưỡng, calo, protein, chất béo, carb,
        - chế độ ăn (ăn chay, keto, giảm cân, tăng cơ...),
        - sức khỏe, lối sống, chế độ tập luyện liên quan đến ăn uống.
        - chức năng, điều khoản, chính sách của ứng dụng.

        Lịch sử hội thoại: {history}

        Quy tắc:
        - Không trả lời các câu hỏi ngoài chủ đề này (hãy từ chối lịch sự).
        - Giải thích ngắn gọn, tự nhiên, rõ ràng.
        - Dựa vào lịch sử trò chuyện để trả lời mạch lạc nếu có câu hỏi nối tiếp.
        """

        try:
            llm = self.llm_service.get_llm()
            response = await llm.ainvoke([
                SystemMessage(content=system_prompt),
                HumanMessage(content=question)
            ], config=config)

            return {"messages": [response]}

        except Exception as e:
            logger.info(f"Lỗi LLM: {e}")
            return {"messages": [AIMessage(content="Xin lỗi, có lỗi xảy ra.")]}

    async def policy(self, state: AgentState, config: RunnableConfig):
        logger.info("---POLICY---")
        messages = state["messages"]
        question = messages[-1].content if messages else state.get("question", "")

        context_text = ""
        try:
            docs = await self.policy_retriever.ainvoke(question)
            if not docs:
                return {"messages": [AIMessage(content="Xin lỗi, tôi không tìm thấy thông tin chính sách liên quan đến câu hỏi của bạn trong hệ thống.")]}
            context_text = "\n\n".join([d.page_content for d in docs])

        except Exception as e:
            logger.info(f"⚠️ Lỗi Policy Retriever: {e}")
            return {"messages": [AIMessage(content="Hệ thống tra cứu chính sách đang gặp sự cố.")]}

        system_prompt = f"""
        Bạn là Trợ lý AI hỗ trợ Chính sách & Quy định của Ứng dụng.

        NHIỆM VỤ:
        Trả lời câu hỏi người dùng CHỈ DỰA TRÊN thông tin được cung cấp dưới đây.

        THÔNG TIN THAM KHẢO:
        {context_text}

        QUY TẮC AN TOÀN:
        1. Nếu thông tin không có trong phần tham khảo, hãy trả lời: "Xin lỗi, hiện tại trong tài liệu chính sách không đề cập đến vấn đề này."
        2. Không được tự bịa ra chính sách hoặc đoán mò.
        3. Trả lời ngắn gọn, đi thẳng vào vấn đề.
        """
        
        try:
            llm = self.llm_service.get_llm()
            response = await llm.ainvoke([
                SystemMessage(content=system_prompt),
                HumanMessage(content=question)
            ], config=config)

            return {"messages": [response]}

        except Exception as e:
            logger.info(f"Lỗi LLM: {e}")
            return {"messages": [AIMessage(content="Xin lỗi, có lỗi xảy ra.")]}

    # --- Routing Helpers ---
    @staticmethod
    def route_initial(state: AgentState):
        topic = state.get("topic")
        non_empty_keys = [key for key, value in TOPIC_REQUIREMENTS.items() if value]
        if topic in non_empty_keys:
            return "load_context"
        return topic

    @staticmethod
    def route_post_validation(state: AgentState):
        if not state.get("is_valid"):
            return "ask_info"

        topic = state.get("topic")
        return topic
