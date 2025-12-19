from langchain_core.messages import AIMessage
from chatbot.agents.states.state import AgentState
from chatbot.models.llm_setup import llm
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.runnables import RunnableConfig
import logging

# --- Cấu hình logging ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def generate_final_response(state: AgentState, config: RunnableConfig):
    print("---NODE: FINAL RESPONSE (FULL NUTRITION AI SUMMARY)---")

    # 1. Lấy dữ liệu từ State
    menu = state.get("final_menu", [])
    profile = state.get("user_profile", {})

    if not menu:
        return {"messages": [AIMessage(content="Xin lỗi, tôi chưa thể tạo thực đơn lúc này.")]}

    # 2. Chuẩn bị bối cảnh thực đơn chi tiết (Full Macros)
    meal_priority = {"sáng": 1, "trưa": 2, "tối": 3}
    sorted_menu = sorted(
        menu,
        key=lambda x: meal_priority.get(x.get('assigned_meal', '').lower(), 99)
    )

    # Tính toán tổng dinh dưỡng thực tế của cả thực đơn để gửi cho AI nhận xét
    actual_total = {"kcal": 0, "p": 0, "f": 0, "c": 0}
    menu_context = ""

    for dish in sorted_menu:
        # Lấy giá trị dinh dưỡng
        k = dish.get('final_kcal', 0)
        p = dish.get('final_protein', 0)
        f = dish.get('final_totalfat', 0)
        c = dish.get('final_carbs', 0)
        
        # Cộng dồn tổng
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

    # 3. Thiết lập System Prompt tập trung vào sự cân bằng chất
    target_kcal = int(profile.get('targetcalories', 0))
    target_p = int(profile.get('protein', 0))
    # Ước tính mục tiêu F/C nếu app có lưu (giả định có trong profile)
    target_f = int(profile.get('totalfat', 0))
    target_c = int(profile.get('carbs', 0))

    system_prompt = f"""
Bạn là một Chuyên gia Dinh dưỡng AI. Hãy trình bày thực đơn và phân tích sâu về các chỉ số dinh dưỡng.

DỮ LIỆU THỰC ĐƠN:
{menu_context}

TỔNG DINH DƯỠNG THỰC TẾ:
- Tổng: {actual_total['kcal']} Kcal | {actual_total['p']}g P | {actual_total['f']}g F | {actual_total['c']}g C

MỤC TIÊU CỦA NGƯỜI DÙNG:
- Mục tiêu: {target_kcal} Kcal | {target_p}g P | {target_f}g F | {target_c}g C

YÊU CẦU TRÌNH BÀY:
1. Trình bày danh sách món ăn theo từng bữa (Sử dụng Markdown đẹp).
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
    print(f"👉 Prompt: {system_prompt}")

    # 4. Gọi LLM Stream
    try:
        response = await llm.ainvoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content="Hãy phân tích thực đơn đầy đủ các chất giúp tôi.")
        ], config=config)

        return {"messages": [response]}

    except Exception as e:
        print(f"Lỗi LLM: {e}")
        return {"messages": [AIMessage(content="Xin lỗi, có lỗi xảy ra.")]}
    