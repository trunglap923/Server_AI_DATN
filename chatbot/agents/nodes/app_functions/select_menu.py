from langchain_core.pydantic_v1 import BaseModel, Field
from typing import Literal, List
from collections import defaultdict
import logging
from chatbot.agents.states.state import AgentState
from chatbot.models.llm_setup import llm
import time

# --- Cấu hình logging ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- DATA MODELS ---
class SelectedDish(BaseModel):
    dish_id: str = Field(description="ID duy nhất của món ăn (được ghi trong dấu ngoặc vuông [ID: ...])")
    meal_type: str = Field(description="Bữa ăn (sáng/trưa/tối)")
    role: Literal["main", "carb", "side"] = Field(
        description="Vai trò: 'main' (Món mặn/Đạm), 'carb' (Cơm/Tinh bột), 'side' (Rau/Canh)"
    )

class DailyMenuStructure(BaseModel):
    dishes: List[SelectedDish] = Field(description="Danh sách các món ăn được chọn")

def select_menu_structure(state: AgentState):
    logger.info("---NODE: AI SELECTOR (FULL MACRO AWARE)---")
    profile = state.get("user_profile", {})
    full_pool = state.get("candidate_pool", [])
    meals_req = state.get("meals_to_generate", [])
    
    if len(full_pool) == 0:
        logger.warning("⚠️ Danh sách ứng viên rỗng, không thể chọn món.")
        return {"selected_structure": []}

    # 1. TÍNH TOÁN MỤC TIÊU CHI TIẾT TỪNG BỮA
    daily_targets = {
        "kcal": float(profile.get('targetcalories', 0)),
        "protein": float(profile.get('protein', 0)),
        "totalfat": float(profile.get('totalfat', 0)),
        "carbs": float(profile.get('carbohydrate', 0))
    }
    ratios = {"sáng": 0.25, "trưa": 0.40, "tối": 0.35}

    meal_targets = {}
    for meal, ratio in ratios.items():
        meal_targets[meal] = {
            k: int(v * ratio) for k, v in daily_targets.items()
        }

    # --- LOGIC TẠO HƯỚNG DẪN ĐỘNG CHO PROMPT ---
    avoid_items = ", ".join(profile.get('Kiêng', []))
    limit_items = ", ".join(profile.get('Hạn chế', []))
    health_condition = profile.get('healthStatus', 'Bình thường')

    safety_instruction = ""
    if health_condition and health_condition.strip() not in  ["Bình thường", "Không có", "Khỏe mạnh"]:
        safety_instruction += f"- Tình trạng sức khỏe: {health_condition}.\n"
    if avoid_items:
        safety_instruction += f"- TUYỆT ĐỐI TRÁNH: {avoid_items}. (Nếu thấy món chứa thành phần này trong danh sách, hãy BỎ QUA ngay lập tức).\n"
    if limit_items:
        safety_instruction += f"- HẠN CHẾ TỐI ĐA: {limit_items}.\n"
    if safety_instruction:
        safety_instruction = f"\nNGUYÊN TẮC AN TOÀN:\n{safety_instruction}\n"
        
    # 2. TIỀN XỬ LÝ & PHÂN NHÓM CANDIDATES
    primary_pool = [m for m in full_pool if not m.get("is_fallback", False)]
    backup_pool = [m for m in full_pool if m.get("is_fallback", False)]

    primary_text = format_pool_detailed(primary_pool, "KHO MÓN ĂN NGON (Ưu tiên dùng)")
    backup_text = format_pool_detailed(backup_pool, "KHO LƯƠNG THỰC CƠ BẢN")

    # 3. XÂY DỰNG PROMPT
    def get_target_str(meal):
        t = meal_targets.get(meal, {})
        return f"{t.get('kcal')} Kcal (P: {t.get('protein')}g, Fat: {t.get('totalfat')}g, Carb: {t.get('carbs')}g)"

    system_prompt = f"""
Vai trò: Đầu bếp trưởng kiêm Chuyên gia dinh dưỡng.
Nhiệm vụ: Ghép thực đơn cho: {', '.join(meals_req)}.

MỤC TIÊU CỤ THỂ TỪNG BỮA (Hãy nhẩm tính để chọn món sát với mục tiêu nhất):
{f"- SÁNG: ~{get_target_str('sáng')}" if 'sáng' in meals_req else ""}
{f"- TRƯA: ~{get_target_str('trưa')}" if 'trưa' in meals_req else ""}
{f"- TỐI : ~{get_target_str('tối')}" if 'tối' in meals_req else ""}
{safety_instruction}

DỮ LIỆU ĐẦU VÀO (Định dạng: [ID] Tên món - Dinh dưỡng):
{primary_text}
{backup_text}

NGUYÊN TẮC CHỌN MÓN (QUAN TRỌNG):
1. Cấu trúc & Dinh dưỡng (Linh hoạt):
  - SÁNG: 1 Món chính (Ưu tiên món nước/bánh mì).
  - TRƯA & TỐI: Không bắt buộc phải đủ 3 món. Hãy chọn theo 1 trong 2 cách sau:
    + Cách A (Món hỗn hợp): Chọn 1-2 món nếu món đó là món hỗn hợp (VD: Bún, Mì, Nui, Cơm rang, Salad thịt...) và đã cung cấp đủ Kcal/Protein/Carb gần với Target.
    + Cách B (Cơm gia đình): Nếu chọn món mặn rời ít Carb hãy ghép thêm [Tinh Bột], nếu ít Rau hãy thêm [Rau/Canh] để cân bằng.
    => MỤC TIÊU: Tổng Kcal của bữa ăn phải sát với Target (sai số cho phép ~10-15%).

2. Quy tắc Ưu tiên & Dự phòng:
  - Luôn quét trong "KHO MÓN ĂN NGON" trước.
  - Nếu chọn Cách B: Hãy tìm món canh/rau trong kho ngon trước. Chỉ khi kho ngon không có hoặc làm vỡ Target Kcal (quá cao), mới lấy Cơm/Rau từ "KHO LƯƠNG THỰC CƠ BẢN".

3. Chiến thuật ghép món:
  - Nếu Target bữa thấp (<500k): Ưu tiên 1 món hỗn hợp nhẹ hoặc bộ 3 món (Cá/Hấp + Cơm ít + Canh rau).
  - Nếu Target bữa cao (>700k): Ưu tiên bộ 3 món đầy đủ hoặc món hỗn hợp đậm đà.
"""

    logger.info("Prompt:")
    logger.info(system_prompt)

    try:
        logger.info("Đang gọi LLM lựa chọn món...")
        llm_structured = llm.with_structured_output(DailyMenuStructure, strict=True)
        
        time_start = time.time()
        result = llm_structured.invoke(system_prompt)
        time_end = time.time()
        logger.info(f"LLM chọn món thành công trong {int((time_end - time_start)*1000)} ms.")
        
        if not result or not hasattr(result, 'dishes'):
            raise ValueError("LLM trả về kết quả rỗng hoặc sai định dạng object.")

    except Exception as e:
        logger.error(f"🔥 LỖI GỌI LLM SELECTOR: {e}")
        return {"selected_structure": [], "reason": "Lỗi hệ thống khi chọn món."}
    
    
    all_clean_candidates = primary_pool + backup_pool
    candidate_map = {str(m.get('id') or m.get('meal_id')): m for m in all_clean_candidates}
    
    def print_menu_by_meal(daily_menu, lookup_map):
        menu_by_meal = defaultdict(list)

        for dish in daily_menu.dishes:
            menu_by_meal[dish.meal_type.lower()].append(dish)

        meal_order = ["sáng", "trưa", "tối"]

        for meal in meal_order:
            if meal in menu_by_meal:
                logger.info(f"\n🍽 Bữa {meal.upper()}:")
                for d in menu_by_meal[meal]:
                    d_id = str(d.dish_id)
                    if d_id in lookup_map:
                        d_name = lookup_map[d_id]['name']
                        logger.info(f" - [ID:{d_id}] {d_name} ({d.role})")
                    else:
                        logger.info(f" - [ID:{d_id}] ??? (Không tìm thấy trong kho) ({d.role})")

    logger.info("\n--- MENU ĐÃ CHỌN ---")
    print_menu_by_meal(result, candidate_map)

    # 4. HẬU XỬ LÝ (Gán Bounds)
    selected_full_info = []

    for choice in result.dishes:
        chosen_id = str(choice.dish_id)
        if chosen_id in candidate_map:
            dish_data = candidate_map[chosen_id].copy()
            dish_data["assigned_meal"] = choice.meal_type

            d_kcal = float(dish_data.get("kcal", 0))
            d_pro = float(dish_data.get("protein", 0))

            t_target = meal_targets.get(choice.meal_type.lower(), {})
            t_kcal = t_target.get("kcal", 500)
            t_pro = t_target.get("protein", 30)

            # --- GIAI ĐOẠN 1: TỰ ĐỘNG SỬA SAI VAI TRÒ ---
            final_role = choice.role
            # 1. Phát hiện "Carb trá hình" (Cơm chiên/Mì xào quá nhiều thịt)
            if final_role == "carb" and d_pro > 15:
                logger.info(f"   ⚠️ Phát hiện Carb giàu đạm ({dish_data['name']}: {d_pro}g Pro). Đổi role sang 'main'.")
                final_role = "main"
            # 2. Phát hiện "Side giàu đạm" (Salad gà/bò, Canh sườn)
            elif final_role == "side" and d_pro > 10:
                logger.info(f"   ⚠️ Phát hiện Side giàu đạm ({dish_data['name']}: {d_pro}g Pro). Đổi role sang 'main'.")
                final_role = "main"
                
            dish_data["role"] = final_role

            # --- GIAI ĐOẠN 2: THIẾT LẬP BOUNDS CƠ BẢN ---
            lower_bound = 0.5
            upper_bound = 1.5

            if final_role == "carb":
                # Cơm/Bún thuần: Cho phép co dãn cực mạnh để bù Kcal
                lower_bound, upper_bound = 0.4, 3.0

            elif final_role == "side":
                # Rau/Canh: Co dãn rộng để bù thể tích ăn
                lower_bound, upper_bound = 0.5, 2.0

            elif final_role == "main":
                # Món mặn: Co dãn vừa phải để giữ hương vị
                lower_bound, upper_bound = 0.6, 1.8


            # --- GIAI ĐOẠN 3: KIỂM TRA AN TOÀN & GHI ĐÈ ---
            # Override A: Nếu món Main có Protein quá lớn so với Target
            if final_role == "main" and d_pro > t_pro:
                logger.info(f"   ⚠️ Món {dish_data['name']} thừa đạm ({d_pro}g > {t_pro}g). Mở rộng bound xuống thấp.")
                lower_bound = 0.3
                upper_bound = min(upper_bound, 1.2)

            # Override B: Nếu món quá nhiều Calo (Chiếm > 80% Kcal cả bữa)
            if d_kcal > (t_kcal * 0.8):
                logger.info(f"   ⚠️ Món {dish_data['name']} quá đậm năng lượng ({d_kcal} kcal). Siết chặt bound.")
                lower_bound = 0.3
                upper_bound = min(upper_bound, 1.0)

            # Override C: Nếu là món Side nhưng Protein vẫn hơi cao (5-10g)
            if final_role == "side" and d_pro > 5:
                logger.info(f"   ⚠️ Món {dish_data['name']} Side có đạm hơi cao ({d_pro}g). Hạ thấp bound.")
                lower_bound = 0.2

            # --- KẾT THÚC: GÁN VÀO DỮ LIỆU ---
            dish_data["solver_bounds"] = (lower_bound, upper_bound)
            selected_full_info.append(dish_data)

    return {
        "selected_structure": selected_full_info,
    }
    
def format_pool_detailed(pool, title):
    if not pool: return ""
    text = f"--- {title} ---\n"
    for m in pool:
        d_id = m.get('id') or m.get('meal_id') 
        name = m['name']
        stats = f"({int(m.get('kcal',0))}k, P:{int(m.get('protein',0))}, F:{int(m.get('totalfat',0))}, C:{int(m.get('carbs',0))})"
        text += f"- [ID: {d_id}] {name} {stats}\n"

    return text