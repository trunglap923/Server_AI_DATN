import random
import logging
from chatbot.agents.states.state import AgentState
from chatbot.agents.tools.food_retriever import food_retriever_50, docsearch
from chatbot.knowledge.vibe import vibes_cooking, vibes_flavor, vibes_healthy, vibes_soup_veg, vibes_style

STAPLE_IDS = ["112", "1852", "2236", "2386", "2388"]

# --- Cấu hình logging ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def generate_food_candidates(state: AgentState):
    logger.info("---NODE: RETRIEVAL CANDIDATES (ADVANCED PROFILE)---")
    meals = state.get("meals_to_generate", [])
    profile = state["user_profile"]

    candidates = []
    
    # 1. NẠP KHO DỰ PHÒNG TỪ ELASTICSEARCH (BY ID)
    try:
        staples_data = fetch_staples_by_ids(docsearch, STAPLE_IDS)
        
        if not staples_data: 
            staples_data = []

        for staple in staples_data:
            name_lower = staple.get("name", "").lower() 
            
            target_meals = []
            if any(x in name_lower for x in ["cơm", "canh", "rau", "kho", "đậu"]):
                target_meals = ["trưa", "tối"]
            elif any(x in name_lower for x in ["bánh mì", "xôi", "trứng", "bún", "phở"]):
                target_meals = ["sáng"]
            else:
                target_meals = ["sáng", "trưa", "tối"]

            for meal in target_meals:
                if meal in meals:
                    s_copy = staple.copy()
                    s_copy["meal_type_tag"] = meal
                    s_copy["retrieval_vibe"] = "Món ăn kèm cơ bản"
                    candidates.append(s_copy)
                    
    except Exception as e:
        logger.warning(f"⚠️ Lỗi khi nạp Staples (Kho dự phòng): {e}")

    # 2. XỬ LÝ DỮ LIỆU PROFILE NGƯỜI DÙNG
    diet_mode = profile.get('diet', '')       # VD: Chế độ HighProtein
    restrictions = profile.get('limitFood', '') # VD: Dị ứng sữa, Thuần chay
    health_status = profile.get('healthStatus', '') # VD: Suy thận

    constraint_prompt = ""
    if restrictions:
        constraint_prompt += f"Yêu cầu bắt buộc: {restrictions}. "
    if health_status not in ["Khỏe mạnh", "Không có", "Bình thường", None]:
        constraint_prompt += f"Phù hợp người bệnh: {health_status}. "
    if diet_mode:
        constraint_prompt += f"Chế độ: {diet_mode}."

    prompt_templates = {
        "sáng": f"Món ăn sáng, điểm tâm. Ưu tiên món nước hoặc món khô dễ tiêu hóa. {constraint_prompt}",
        "trưa": f"Món ăn chính cho bữa trưa. {constraint_prompt}",
        "tối":  f"Món ăn tối, nhẹ bụng. {constraint_prompt}",
    }

    for meal_type in meals:
        try:
            logger.info(meal_type)
            base_prompt = prompt_templates.get(meal_type, f"Món ăn {meal_type}. {constraint_prompt}")
            
            try:
                vibe = get_random_vibe(meal_type)
                numerical_query = generate_numerical_constraints(profile, meal_type)
            except Exception as sub_e:
                logger.error(f"Lỗi logic phụ (vibe/numerical) cho bữa {meal_type}: {sub_e}")
                vibe = "Hài hòa"
                numerical_query = ""

            final_query = f"{base_prompt} Phong cách: {vibe}.{' Ràng buộc: ' + numerical_query if numerical_query else ''}"
            logger.info(f"🔎 Query ({meal_type}): {final_query}")

            docs = food_retriever_50.invoke(final_query)
            if not docs:
                logger.warning(f"⚠️ Retriever trả về rỗng cho bữa: {meal_type}")
                continue

            ranked_items = rank_candidates(docs, profile, meal_type)
            
            if ranked_items:
                top_n_count = min(len(ranked_items), 30)
                top_candidates = ranked_items[:top_n_count]
                random.shuffle(top_candidates)
                
                k = min(20, top_n_count) if len(meals) == 1 else min(10, top_n_count)
                selected_docs = top_candidates[:k]

                for item in selected_docs:
                    candidate = item.copy()
                    candidate["meal_type_tag"] = meal_type
                    candidate["retrieval_vibe"] = vibe
                    candidates.append(candidate)
        
        except Exception as e:
            logger.error(f"🔥 LỖI NGHIÊM TRỌNG khi retrieve bữa {meal_type}: {e}")
            continue

    unique_candidates = {v.get('name', 'Unknown'): v for v in candidates}.values()
    final_pool = list(unique_candidates)
    logger.info(f"📚 Candidate Pool Size: {len(final_pool)} món")
    if len(final_pool) == 0:
        logger.critical("❌ KHÔNG TÌM THẤY MÓN NÀO! Check lại DB connection.")
    return {"candidate_pool": final_pool, "meals_to_generate": meals}

def generate_numerical_constraints(user_profile, meal_type):
    """
    Tạo chuỗi ràng buộc số liệu dinh dưỡng dựa trên cấu hình người dùng.
    """
    ratios = {"sáng": 0.25, "trưa": 0.40, "tối": 0.35}
    meal_ratio = ratios.get(meal_type, 0.3)

    critical_nutrients = {
        "Protein": ("protein", "protein", "g", "range"),
        "Saturated fat": ("saturatedfat", "saturatedfat", "g", "max"),
        "Natri": ("natri", "natri", "mg", "max"),
        "Kali": ("kali", "kali", "mg", "range"),
        "Phốt pho": ("photpho", "photpho", "mg", "max"),
        "Sugars": ("sugar", "sugar", "g", "max"),
        "Carbohydrate": ("carbohydrate", "carbs", "g", "range"),
    }

    constraints = []

    check_list = set(user_profile.get('Kiêng', []) + user_profile.get('Hạn chế', []))
    
    if "thận" in user_profile.get('healthStatus', '').lower():
        check_list.update(["Protein", "Natri", "Kali", "Phốt pho"])
    
    for item_name in check_list:
        if item_name not in critical_nutrients: continue

        config = critical_nutrients.get(item_name)
        profile_key, db_key, unit, logic = config
        daily_val = float(user_profile.get(profile_key, 0))
        meal_target = daily_val * meal_ratio

        if logic == 'max':
            # Nới lỏng một chút ở bước tìm kiếm (120-130% target) để không bị lọc hết
            threshold = round(meal_target * 1.3, 2)
            constraints.append(f"{db_key} < {threshold}{unit}")

        elif logic == 'range':
            # Range rộng (50% - 150%) để bắt được nhiều món
            min_val = round(meal_target * 0.5, 2)
            max_val = round(meal_target * 1.5, 2)
            constraints.append(f"{db_key} > {min_val}{unit} - {db_key} < {max_val}{unit}")

    if not constraints: return ""
    return ", ".join(constraints)

def rank_candidates(candidates, user_profile, meal_type):
    """
    Chấm điểm (Scoring) các món ăn dựa trên cấu hình dinh dưỡng chi tiết.
    """
    print("---NODE: RANKING CANDIDATES (ADVANCED SCORING)---")

    ratios = {"sáng": 0.25, "trưa": 0.40, "tối": 0.35}
    meal_ratio = ratios.get(meal_type, 0.3)

    nutrient_config = {
        # --- Nhóm Đa lượng (Macro) ---
        "Protein": ("protein", "protein", "g", "range"),
        "Total Fat": ("totalfat", "totalfat", "g", "max"),
        "Carbohydrate": ("carbohydrate", "carbs", "g", "range"),
        "Saturated fat": ("saturatedfat", "saturatedfat", "g", "max"),
        "Monounsaturated fat": ("monounsaturatedfat", "monounsaturatedfat", "g", "max"),
        "Trans fat": ("transfat", "transfat", "g", "max"),
        "Sugars": ("sugar", "sugar", "g", "max"),
        "Chất xơ": ("fiber", "fiber", "g", "min"),

        # --- Nhóm Vi chất (Micro) ---
        "Vitamin A": ("vitamina", "vitamina", "mg", "min"),
        "Vitamin C": ("vitaminc", "vitaminc", "mg", "min"),
        "Vitamin D": ("vitamind", "vitamind", "mg", "min"),
        "Vitamin E": ("vitamine", "vitamine", "mg", "min"),
        "Vitamin K": ("vitamink", "vitamink", "mg", "min"),
        "Vitamin B6": ("vitaminb6", "vitaminb6", "mg", "min"),
        "Vitamin B12": ("vitaminb12", "vitaminb12", "mg", "min"),

        # --- Khoáng chất ---
        "Canxi": ("canxi", "canxi", "mg", "min"),
        "Sắt": ("fe", "fe", "mg", "min"),
        "Magie": ("magie", "magie", "mg", "min"),
        "Kẽm": ("zn", "zn", "mg", "min"),
        "Kali": ("kali", "kali", "mg", "range"),
        "Natri": ("natri", "natri", "mg", "max"),
        "Phốt pho": ("photpho", "photpho", "mg", "max"),

        # --- Khác ---
        "Cholesterol": ("cholesterol", "cholesterol", "mg", "max"),
        "Choline": ("choline", "choline", "mg", "min"),
        "Caffeine": ("caffeine", "caffeine", "mg", "max"),
        "Alcohol": ("alcohol", "alcohol", "g", "max"),
    }

    scored_list = []

    for doc in candidates:
        item = doc.metadata
        score = 0
        reasons = [] # Lưu lý do để debug hoặc giải thích cho user

        # --- 1. CHẤM ĐIỂM NHÓM "BỔ SUNG" (BOOST) ---
        # Logic: Càng nhiều càng tốt
        for nutrient in user_profile.get('Bổ sung', []):
            config = nutrient_config.get(nutrient)
            if not config: continue

            p_key, db_key, unit, logic = config

            # Lấy giá trị thực tế trong món ăn và mục tiêu
            val = float(item.get(db_key, 0))
            daily_target = float(user_profile.get(p_key, 0))
            meal_target = daily_target * meal_ratio

            if meal_target == 0: continue

            # Chấm điểm
            # Nếu đạt > 50% target bữa -> +10 điểm
            if val >= meal_target * 0.5:
                score += 10
                reasons.append(f"Giàu {nutrient}")
            # Nếu đạt > 80% target -> +15 điểm (thưởng thêm)
            if val >= meal_target * 0.8:
                score += 5

        # --- 2. CHẤM ĐIỂM NHÓM "HẠN CHẾ" & "KIÊNG" (PENALTY/REWARD) ---
        # Gộp chung: Càng thấp càng tốt
        check_list = set(user_profile.get('Hạn chế', []) + user_profile.get('Kiêng', []))

        for nutrient in check_list:
            config = nutrient_config.get(nutrient)
            if not config: continue

            p_key, db_key, unit, logic = config
            val = float(item.get(db_key, 0))
            daily_target = float(user_profile.get(p_key, 0))
            meal_target = daily_target * meal_ratio

            if meal_target == 0: continue

            if logic == 'max':
                # Nếu thấp hơn target -> +10 điểm (Tốt)
                if val <= meal_target:
                    score += 10
                # Nếu thấp hơn hẳn (chỉ bằng 50% target) -> +15 điểm (Rất an toàn)
                if val <= meal_target * 0.5:
                    score += 5
                # Nếu vượt quá target -> -10 điểm (Phạt)
                if val > meal_target:
                    score -= 10

            elif logic == 'range':
                # Logic cho Kali/Protein: Tốt nhất là nằm trong khoảng, không thấp quá, không cao quá
                min_safe = meal_target * 0.5
                max_safe = meal_target * 1.5

                if min_safe <= val <= max_safe:
                    score += 10 # Nằm trong vùng an toàn
                elif val > max_safe:
                    score -= 10 # Cao quá (nguy hiểm cho thận)
                # Thấp quá thì không trừ điểm nặng, chỉ không được cộng

        # --- 3. ĐIỂM THƯỞNG CHO SỰ PHÙ HỢP CƠ BẢN (BASE HEALTH) ---
        if float(item.get('sugar', 0)) < 5: score += 2
        if float(item.get('saturated_fat', 0)) < 3: score += 2
        if float(item.get('fiber', 0)) > 3: score += 3

        # Lưu kết quả
        item_copy = item.copy()
        item_copy["health_score"] = score
        item_copy["score_reason"] = ", ".join(reasons[:3]) # Chỉ lấy 3 lý do chính
        scored_list.append(item_copy)

    # 4. SẮP XẾP & TRẢ VỀ
    scored_list.sort(key=lambda x: x["health_score"], reverse=True)

    # # Debug: In Top 3
    # logger.info("🏆 Top 3 Món Tốt Nhất (Sau khi chấm điểm):")
    # for i, m in enumerate(scored_list[:3]):
    #     logger.info(f"   {i+1}. {m['name']} (Score: {m['health_score']}) | {m.get('score_reason')}")

    return scored_list

def get_random_vibe(meal_type):
    """
    Chọn vibe thông minh với xác suất cao ra món Thanh đạm/Canh cho bữa Trưa/Tối
    """

    # --- BỮA SÁNG ---
    if meal_type == "sáng":
        pool = [
            "khởi đầu ngày mới năng lượng",
            "món nước nóng hổi",
            "chế biến nhanh gọn lẹ",
            "điểm tâm nhẹ nhàng",
            "hương vị thanh tao"
        ] + vibes_flavor
        return random.choice(pool)

    # --- BỮA TRƯA / TỐI ---
    else:
        roll = random.random()

        if roll < 0.3:
            # 30%: Query tập trung vào Món Mặn Đậm Đà (Thịt/Cá kho, chiên...)
            # "Kho tộ đậm đà mang hương vị đồng quê"
            v_main = random.choice(vibes_cooking)
            v_style = random.choice(vibes_style)
            return f"{v_main} mang {v_style}"

        elif roll < 0.6:
            # 30%: Query tập trung hoàn toàn vào Món Thanh Đạm/Canh
            # "Canh hầm thanh mát bổ dưỡng mang hương vị thanh đạm nhẹ nhàng"
            v_soup = random.choice(vibes_soup_veg)
            v_flavor = random.choice(vibes_healthy + vibes_flavor)
            return f"{v_soup} mang {v_flavor}"

        else:
            # 40%: Query HỖN HỢP (Kỹ thuật "Combo Keyword")
            # "Kho tộ đậm đà kết hợp với canh rau thanh mát"
            v_main = random.choice(vibes_cooking)
            v_soup = random.choice(vibes_soup_veg)
            return f"{v_main} kết hợp với {v_soup}"
        
def fetch_staples_by_ids(vectorstore, doc_ids):
    """
    Lấy document từ ES theo ID và map về đúng định dạng candidate_pool.
    """
    if not doc_ids:
        return []

    try:
        client = vectorstore.client

        # 1. Gọi API mget để lấy dữ liệu thô cực nhanh
        response = client.mget(index="food_v2_vdb", body={"ids": doc_ids})

        fetched_items = []

        for doc in response['docs']:
            if doc['found']:
                # Dữ liệu gốc trong ES
                src = doc['_source']

                meta = src.get('metadata', src)

                # 2. Mapping chi tiết theo mẫu bạn cung cấp
                item = {
                    # --- ĐỊNH DANH ---
                    'meal_id': meta.get('meal_id', doc['_id']), # Fallback về doc_id nếu ko có meal_id
                    'name': meta.get('name', 'Món không tên'),

                    # --- THÀNH PHẦN ---
                    'ingredients': meta.get('ingredients', []),
                    'ingredients_text': meta.get('ingredients_text', ''),
                    'tags': meta.get('tags', []),

                    # --- CÁCH LÀM ---
                    'preparation_steps': meta.get('preparation_steps', ''),
                    'cooking_steps': meta.get('cooking_steps', ''),

                    # --- DINH DƯỠNG ---
                    'kcal': float(meta.get('kcal', 0.0)),
                    'carbs': float(meta.get('carbs', 0.0)),
                    'protein': float(meta.get('protein', 0.0)),
                    'totalfat': float(meta.get('totalfat', 0.0) or meta.get('lipid', 0.0)), # Handle alias

                    # --- VI CHẤT ---
                    'sugar': float(meta.get('sugar', 0.0)),
                    'fiber': float(meta.get('fiber', 0.0)),
                    'saturatedfat': float(meta.get('saturatedfat', 0.0)),
                    'monounsaturatedfat': float(meta.get('monounsaturatedfat', 0.0)),
                    'polyunsaturatedfat': float(meta.get('polyunsaturatedfat', 0.0)),
                    'transfat': float(meta.get('transfat', 0.0)),
                    'cholesterol': float(meta.get('cholesterol', 0.0)),

                    # Vitamin & Khoáng (Map theo mẫu)
                    'vitamina': float(meta.get('vitamina', 0.0)),
                    'vitamind': float(meta.get('vitamind', 0.0)),
                    'vitaminc': float(meta.get('vitaminc', 0.0)),
                    'vitaminb6': float(meta.get('vitaminb6', 0.0)),
                    'vitaminb12': float(meta.get('vitaminb12', 0.0)),
                    'vitamine': float(meta.get('vitamine', 0.0)),
                    'vitamink': float(meta.get('vitamink', 0.0)),
                    'choline': float(meta.get('choline', 0.0)),
                    'canxi': float(meta.get('canxi', 0.0)),
                    'fe': float(meta.get('fe', 0.0)),
                    'magie': float(meta.get('magie', 0.0)),
                    'photpho': float(meta.get('photpho', 0.0)),
                    'kali': float(meta.get('kali', 0.0)),
                    'natri': float(meta.get('natri', 0.0)),
                    'zn': float(meta.get('zn', 0.0)),
                    'water': float(meta.get('water', 0.0)),
                    'caffeine': float(meta.get('caffeine', 0.0)),
                    'alcohol': float(meta.get('alcohol', 0.0)),

                    # --- AI LOGIC FIELDS ---
                    'health_score': 5,
                    'score_reason': 'Món ăn cơ bản (Staple Food)',
                    'meal_type_tag': '', # Sẽ điền sau
                    'retrieval_vibe': 'Món ăn kèm cơ bản',

                    # Cờ fallback
                    'is_fallback': True
                }

                fetched_items.append(item)

        return fetched_items

    except Exception as e:
        print(f"⚠️ Lỗi fetch staples từ ES: {e}")
        return []