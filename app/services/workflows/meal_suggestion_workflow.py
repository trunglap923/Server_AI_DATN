import logging
import asyncio
import time
import random
import requests
from typing import List, Dict, Any, Literal
from collections import defaultdict

from langgraph.graph import StateGraph, END
from langchain_core.pydantic_v1 import BaseModel, Field

from app.schema.agent_state import AgentState
from app.services.core.llm_service import LLMService
from app.services.core.retrieval_service import RetrievalService
from app.services.core.optimization_service import OptimizationService
from app.core.config import settings

try:
    from app.knowledge.vibe import vibes_cooking, vibes_flavor, vibes_healthy, vibes_soup_veg, vibes_style
    from app.knowledge.disease import disease_data, nutrients
except ImportError:
    vibes_cooking = ["đậm đà"]
    vibes_flavor = ["thơm ngon"]
    vibes_healthy = ["thanh đạm"]
    vibes_soup_veg = ["canh rau"]
    vibes_style = ["truyền thống"]
    disease_data = {}
    nutrients = []

logger = logging.getLogger(__name__)

# --- Pydantic Models for Selection ---
class SelectedDish(BaseModel):
    dish_id: str = Field(description="ID duy nhất của món ăn (được ghi trong dấu ngoặc vuông [ID: ...])")
    meal_type: str = Field(description="Bữa ăn (sáng/trưa/tối)")
    role: Literal["main", "carb", "side"] = Field(
        description="Vai trò: 'main' (Món mặn/Đạm), 'carb' (Cơm/Tinh bột), 'side' (Rau/Canh)"
    )

class DailyMenuStructure(BaseModel):
    dishes: List[SelectedDish] = Field(description="Danh sách các món ăn được chọn")

class MealSuggestionWorkflowService:
    def __init__(self, llm_service: LLMService, retrieval_service: RetrievalService, optimization_service: OptimizationService):
        self.llm_service = llm_service
        self.retrieval_service = retrieval_service
        self.optimization_service = optimization_service
        
        self.llm = self.llm_service.get_llm()
        self.retriever_50 = self.retrieval_service.get_food_retriever(k=50)
        self.food_store = self.retrieval_service.food_store
        
        self.STAPLE_IDS = ["112", "1852", "2236", "2386", "2388"]

    def build_graph(self):
        workflow = StateGraph(AgentState)
        
        workflow.add_node("get_profile", self.node_get_profile)
        workflow.add_node("generate_candidates", self.node_generate_candidates)
        workflow.add_node("select_menu", self.node_select_menu)
        workflow.add_node("optimize_macros", self.node_optimize_macros)

        workflow.set_entry_point("get_profile")
        workflow.add_edge("get_profile", "generate_candidates")
        workflow.add_edge("generate_candidates", "select_menu")
        workflow.add_edge("select_menu", "optimize_macros")
        workflow.add_edge("optimize_macros", END)

        return workflow.compile()

    async def run(self, inputs: Dict[str, Any]):
        graph = self.build_graph()
        return await graph.ainvoke(inputs)

    # ================= NODES =================

    async def node_get_profile(self, state: AgentState):
        logger.info("---NODE: GET USER PROFILE---")
        user_id = state.get("user_id", 1)
        user_profile = state.get("user_profile", None)

        if not user_profile:
            raw_profile = self._fetch_user_profile(user_id)
            restrictions = self._get_restrictions(raw_profile.get("healthStatus", ""))
            final_profile = {**raw_profile, **restrictions}
        else:
            final_profile = user_profile

        return {"user_profile": final_profile}

    async def node_generate_candidates(self, state: AgentState):
        logger.info("---NODE: RETRIEVAL CANDIDATES---")
        meals = state.get("meals_to_generate", [])
        profile = state["user_profile"]

        candidates = []

        # 1. Fetch Staples
        try:
            staples_data = self._fetch_staples_by_ids(self.STAPLE_IDS)
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
            logger.warning(f"⚠️ Error fetching staples: {e}")

        # 2. Build Reason
        dynamic_reason = self._build_reason(profile)

        # 3. Process Meals
        prompt_templates = self._build_prompt_templates(profile)
        
        tasks = [
            self._process_single_meal(meal, profile, prompt_templates) 
            for meal in meals
        ]
        if tasks:
            results = await asyncio.gather(*tasks)
            for res in results:
                candidates.extend(res)

        unique_candidates = {}
        for item in candidates:
            key = str(item.get('id') or item.get('meal_id') or item.get('name'))
            unique_candidates[key] = item
        
        final_pool = list(unique_candidates.values())
        logger.info(f"📚 Total Candidate Pool: {len(final_pool)} items")
        
        return {"candidate_pool": final_pool, "meals_to_generate": meals, "reason": dynamic_reason}

    async def node_select_menu(self, state: AgentState):
        logger.info("---NODE: AI SELECTOR---")
        profile = state.get("user_profile", {})
        full_pool = state.get("candidate_pool", [])
        meals_req = state.get("meals_to_generate", [])
        
        if not full_pool:
            logger.warning("⚠️ Danh sách ứng viên rỗng, không thể chọn món.")
            return {"selected_structure": []}

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

        # Select Menu Logic using LLM
        primary_pool = [m for m in full_pool if not m.get("is_fallback", False)]
        backup_pool = [m for m in full_pool if m.get("is_fallback", False)]
        
        primary_text = self._format_pool_detailed(primary_pool, "KHO MÓN ĂN NGON")
        backup_text = self._format_pool_detailed(backup_pool, "KHO LƯƠNG THỰC CƠ BẢN")
        
        system_prompt = self._build_selection_prompt(profile, meals_req, primary_text, backup_text, meal_targets)
        logger.info(f"📝 System Prompt: {system_prompt}")  

        try:
            logger.info("Đang gọi LLM lựa chọn món...")
            llm_structured = self.llm.with_structured_output(DailyMenuStructure, strict=True)
            
            time_start = time.time()
            result = await llm_structured.ainvoke(system_prompt) 
            time_end = time.time()
            logger.info(f"✅ Thời gian gọi LLM: {time_end - time_start:.2f} giây")
        except Exception as e:
            logger.error(f"Error calling LLM Selector: {e}")
            return {"selected_structure": []}
            
        candidate_map = {str(m.get('id') or m.get('meal_id')): m for m in full_pool}
        
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

        # Post-processing
        selected_full_info = []
        for choice in result.dishes:
            chosen_id = str(choice.dish_id)
            if chosen_id in candidate_map:
                dish_data = candidate_map[chosen_id].copy()
                dish_data["assigned_meal"] = choice.meal_type
                dish_data["role"] = choice.role
                
                # Apply bounds logic
                dish_data["solver_bounds"] = self._calculate_bounds(dish_data, choice.role, choice.meal_type, meal_targets)
                selected_full_info.append(dish_data)
                
        return {"selected_structure": selected_full_info}

    async def node_optimize_macros(self, state: AgentState):
        profile = state.get("user_profile", {})
        menu = state.get("selected_structure", [])
        
        final_menu = self.optimization_service.optimize_menu(profile, menu)
        
        return {"final_menu": final_menu}

    # ================= HELPERS based on existing logic =================

    def _fetch_user_profile(self, user_id: int):
        url = f"{settings.API_BASE_URL}/get_all_info?id={user_id}"
        default_profile = {'id': 1, 'fullname': 'Default', 'age': 25, 'targetcalories': 2000, 'protein': 100, 'totalfat': 60, 'carbohydrate': 250}
        
        try:
            response = requests.get(url, timeout=3)
            response.raise_for_status()
            result = response.json()
            return {**result.get('userInfo', {}), **result.get('requiredIndex', {})}
        except Exception:
            return default_profile

    def _get_restrictions(self, disease: str):
        result = {"Kiêng": [], "Hạn chế": [], "Bổ sung": []}
        if disease not in disease_data:
            return result
        values = disease_data[disease]
        for nutrient, action in zip(nutrients, values):
            if action in result:
                result[action].append(nutrient)
        return result

    def _fetch_staples_by_ids(self, doc_ids):
        if not doc_ids: return []
        try:
            client = self.food_store.client
            response = client.mget(index="food_v2_vdb", body={"ids": doc_ids})
            fetched = []
            for doc in response['docs']:
                if doc['found']:
                    src = doc['_source']
                    meta = src.get('metadata', src)
                    item = meta.copy()
                    item['meal_id'] = meta.get('meal_id', doc['_id'])
                    item['is_fallback'] = True
                    fetched.append(item)
            return fetched
        except Exception as e:
            logger.warning(f"Error fetching staples: {e}")
            return []

    async def _process_single_meal(self, meal_type, profile, prompt_templates):
        base_prompt = prompt_templates.get(meal_type, f"Món ăn {meal_type}.")
        vibe = self._get_random_vibe(meal_type)
        numerical_query = self._generate_numerical_constraints(profile, meal_type)
        final_query = f"{base_prompt} Phong cách: {vibe}.{' Ràng buộc: ' + numerical_query if numerical_query else ''}"
        logger.info(f"🔎 Query ({meal_type}): {final_query}")

        try:
            time_start = time.time()
            docs = await self.retriever_50.ainvoke(final_query)
            time_end = time.time()
            
            logger.info(f"⏱️ Bữa {meal_type} xong trong {round(time_end - time_start, 2)}s")
            
            if not docs:
                logger.warning(f"⚠️ Không tìm thấy món nào cho bữa: {meal_type}")
                return []

            ranked = self._rank_candidates(docs, profile, meal_type)
            top = ranked[:30]
            random.shuffle(top)
            selected = top[:10]
            
            results = []
            for item in selected:
                c = item.copy()
                c["meal_type_tag"] = meal_type
                c["retrieval_vibe"] = vibe
                results.append(c)
            return results
        except Exception as e:
            logger.error(f"Error processing meal {meal_type}: {e}")
            return []

    def _rank_candidates(self, candidates, user_profile, meal_type):
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
            reasons = []

            # --- 1. CHẤM ĐIỂM NHÓM "BỔ SUNG" ---
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

            # --- 2. CHẤM ĐIỂM NHÓM "HẠN CHẾ" & "KIÊNG" ---
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
                    # Nếu thấp hơn hẳn (chỉ bằng 50% target) -> +15 điểm
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

            # --- 3. ĐIỂM THƯỞNG CHO SỰ PHÙ HỢP CƠ BẢN ---
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
        return scored_list

    def _generate_numerical_constraints(self, user_profile, meal_type):
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
                # Nới lỏng một chút ở bước tìm kiếm (120-150% target) để không bị lọc hết
                threshold = round(meal_target * 1.5, 2)
                constraints.append(f"{db_key} < {threshold}{unit}")

            elif logic == 'range':
                # Range rộng (40% - 160%) để bắt được nhiều món
                min_val = round(meal_target * 0.4, 2)
                max_val = round(meal_target * 1.6, 2)
                constraints.append(f"{db_key} > {min_val}{unit} - {db_key} < {max_val}{unit}")

        if not constraints: return ""
        return ", ".join(constraints)

    def _get_random_vibe(self, meal_type):
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

    def _build_reason(self, profile):
        diet_mode = profile.get('diet', '')       # VD: Chế độ HighProtein
        restrictions = profile.get('limitFood', '') # VD: Dị ứng sữa, Thuần chay
        health_status = profile.get('healthStatus', '') # VD: Suy thận
        
        #--------Reason----------
        raw_limit = str(restrictions) if restrictions else ''
        specific_avoids = [x.strip() for x in raw_limit.split(',')] if raw_limit and raw_limit.lower() not in ["không", "không có"] else []

        raw_kieng = profile.get('Kiêng', [])
        raw_hanche = profile.get('Hạn chế', [])
        list_kieng = raw_kieng if isinstance(raw_kieng, list) else ([str(raw_kieng)] if raw_kieng else [])
        list_hanche = raw_hanche if isinstance(raw_hanche, list) else ([str(raw_hanche)] if raw_hanche else [])
        nutrient_controls = list(set(list_kieng + list_hanche))
        nutrient_controls = [x for x in nutrient_controls if x and x.lower() not in ["không", "không có", "none"]]

        raw_bosung = profile.get('Bổ sung', [])
        list_bosung = raw_bosung if isinstance(raw_bosung, list) else ([str(raw_bosung)] if raw_bosung else [])
        priority_nutrients = set([x for x in list_bosung if x and x.lower() not in ["không", "không có"]])

        reason_parts = []
        
        if diet_mode and diet_mode not in ["Bình thường", None]:
            reason_parts.append(f"theo chế độ **{diet_mode}**")
        if health_status and health_status not in ["Bình thường", "Khỏe mạnh", "Không có", None]:
            reason_parts.append(f"hỗ trợ bệnh **{health_status}**")
        if specific_avoids: reason_parts.append(f"phù hợp với người **{', '.join(specific_avoids)}**")
        if nutrient_controls: reason_parts.append(f"kiểm soát lượng **{', '.join(nutrient_controls)}**")
        if priority_nutrients: reason_parts.append(f"tăng cường thực phẩm giàu **{', '.join(priority_nutrients)}**")

        dynamic_reason = f"Hệ thống đã tối ưu thực đơn: {'; '.join(reason_parts)}." if reason_parts else "Thực đơn cân bằng dinh dưỡng cơ bản."
        return dynamic_reason

    def _build_prompt_templates(self, profile):
        diet_mode = profile.get('diet', '')
        restrictions = profile.get('limitFood', '')
        health_status = profile.get('healthStatus', '')
        
        constraint_prompt = ""
        if restrictions not in ["Không có"]:
            constraint_prompt += f"Yêu cầu bắt buộc: {restrictions}. "
        if health_status not in ["Khỏe mạnh", "Không có", "Bình thường", None]:
            constraint_prompt += f"Phù hợp người bệnh: {health_status}. "
        if diet_mode not in ["Bình thường"]:
            constraint_prompt += f"Chế độ: {diet_mode}."

        prompt_templates = {
            "sáng": f"Món ăn sáng, điểm tâm. Ưu tiên món nước hoặc món khô dễ tiêu hóa. {constraint_prompt}",
            "trưa": f"Món ăn chính cho bữa trưa. {constraint_prompt}",
            "tối":  f"Món ăn tối, nhẹ bụng. {constraint_prompt}",
        }

        return prompt_templates

    def _format_pool_detailed(self, pool, title):
        if not pool: return ""
        text = f"--- {title} ---\n"
        for m in pool:
            d_id = m.get('id') or m.get('meal_id') 
            name = m['name']
            stats = f"({int(m.get('kcal',0))}k, P:{int(m.get('protein',0))}, F:{int(m.get('totalfat',0))}, C:{int(m.get('carbs',0))})"
            text += f"- [ID: {d_id}] {name} {stats}\n"

        return text

    def _build_selection_prompt(self, profile, meals_req, primary_text, backup_text, meal_targets):
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

        return system_prompt

    def _calculate_bounds(self, dish_data, role, meal_type, meal_targets):
        d_kcal = float(dish_data.get("kcal", 0))
        d_pro = float(dish_data.get("protein", 0))

        t_target = meal_targets.get(meal_type.lower(), {})
        t_kcal = t_target.get("kcal", 500)
        t_pro = t_target.get("protein", 30)

        # --- GIAI ĐOẠN 1: TỰ ĐỘNG SỬA SAI VAI TRÒ ---
        final_role = role
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

        return lower_bound, upper_bound

