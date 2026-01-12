import logging
import time
import numpy as np
from typing import List, Dict, Any, Optional
from scipy.optimize import minimize_scalar

from langgraph.graph import StateGraph, END
from langchain_core.pydantic_v1 import BaseModel, Field

from app.schema.agent_state import SwapState
from app.services.core.llm_service import LLMService
from app.services.core.retrieval_service import RetrievalService
from app.services.workflows.meal_suggestion_workflow import MealSuggestionWorkflowService
from app.core.config import settings

logger = logging.getLogger(__name__)

class ChefDecision(BaseModel):
    selected_meal_id: int = Field(description="ID (meal_id) của món ăn được chọn từ danh sách")
    reason: str = Field(description="Lý do ẩm thực ngắn gọn")

class FoodSimilarityWorkflowService:
    def __init__(self, llm_service: LLMService, retrieval_service: RetrievalService, meal_workflow_service: MealSuggestionWorkflowService):
        self.llm_service = llm_service
        self.retrieval_service = retrieval_service
        self.meal_workflow_service = meal_workflow_service
        
        self.llm = self.llm_service.get_llm()
        self.retriever = self.retrieval_service.get_food_retriever(k=10)
        
    def build_graph(self):
        workflow = StateGraph(SwapState)
        
        workflow.add_node("get_profile", self.node_get_profile)
        workflow.add_node("find_candidates", self.node_find_candidates)
        workflow.add_node("optimize_select", self.node_optimize_select)
        workflow.add_node("select_meal", self.node_select_meal)

        workflow.set_entry_point("get_profile")
        workflow.add_edge("get_profile", "find_candidates")
        workflow.add_edge("find_candidates", "optimize_select")
        workflow.add_edge("optimize_select", "select_meal")
        workflow.add_edge("select_meal", END)

        return workflow.compile()

    async def run(self, inputs: Dict[str, Any]):
        graph = self.build_graph()
        return await graph.ainvoke(inputs)

    # ================= NODES =================
    
    async def node_get_profile(self, state: SwapState):
        logger.info("---NODE: GET USER PROFILE (SWAP)---")
        user_id = state.get("user_id", "1")
        user_profile = state.get("user_profile", None)

        if not user_profile:
            raw_profile = self.meal_workflow_service._fetch_user_profile(user_id)
            restrictions = self.meal_workflow_service._get_restrictions(raw_profile.get("healthStatus", ""))
            final_profile = {**raw_profile, **restrictions}
        else:
            final_profile = user_profile

        return {"user_profile": final_profile}

    async def node_find_candidates(self, state: SwapState):
        logger.info("---NODE: FIND REPLACEMENTS---")
        food_old = state.get("food_old")
        profile = state.get("user_profile", {})
        
        if not food_old:
            logger.warning("⚠️ No food_old provided")
            return {"candidates": []}

        diet_mode = profile.get('diet', '')       # VD: Chế độ HighProtein
        restrictions = profile.get('limitFood', '') # VD: Dị ứng sữa, Thuần chay
        health_status = profile.get('healthStatus', '') # VD: Suy thận
        
        constraint_prompt = ""
        if restrictions not in ["Không có"]:
            constraint_prompt += f"Yêu cầu bắt buộc: {restrictions}. "
        if health_status not in ["Khỏe mạnh", "Không có", "Bình thường", None]:
            constraint_prompt += f"Phù hợp người bệnh: {health_status}. "
        if diet_mode not in ["Bình thường"]:
            constraint_prompt += f"Chế độ: {diet_mode}."

        # 1. Trích xuất ngữ cảnh từ món cũ
        role = food_old.get("role", "main")       # VD: main, side, carb
        vibe = food_old.get("retrieval_vibe", "Món ăn kèm cơ bản")          # VD: món nhẹ nhàng, món giàu đạm
        meal_type = food_old.get("assigned_meal", "trưa") # VD: trưa
        old_name = food_old.get("name", "")
        numerical_query = self.meal_workflow_service._generate_numerical_constraints(profile, meal_type)

        # 2. Xây dựng Query tự nhiên để SelfQueryRetriever hiểu
        query = (
            f"Tìm các món ăn đóng vai trò '{role}' phù hợp cho bữa '{meal_type}'. Phong cách: '{vibe}'. "
            f"Khác với món '{old_name}'. "
            f"{constraint_prompt}"
        )

        if numerical_query:
            query += f"Yêu cầu: {numerical_query}"
        logger.info(f"🔎 Query: {query}")
        
        try:
            docs = await self.retriever.ainvoke(query)
            candidates = []
            for doc in docs:
                item = doc.metadata.copy()
                if item.get("name") == old_name: continue
                item["target_role"] = role
                item["target_meal"] = meal_type
                candidates.append(item)
            logger.info(f"📚 Tìm thấy {len(candidates)} ứng viên tiềm năng.")
            return {"candidates": candidates}
        except Exception as e:
            logger.error(f"Error finding candidates: {e}")
            return {"candidates": []}

    async def node_optimize_select(self, state: SwapState):
        logger.info("---NODE: OPTIMIZE SELECT---")
        candidates = state.get("candidates", [])
        food_old = state.get("food_old")
        
        if not candidates or not food_old:
            return {"top_candidates": []}

        old_scale = float(food_old.get("portion_scale", 1.0))
        target_vector = np.array([
            float(food_old.get("kcal", 0)) * old_scale,
            float(food_old.get("protein", 0)) * old_scale,
            float(food_old.get("totalfat", 0)) * old_scale,
            float(food_old.get("carbs", 0)) * old_scale
        ])
        weights = np.array([3.0, 2.0, 1.0, 1.0])
        bounds = food_old.get("solver_bounds", (0.5, 2.0))
        if isinstance(bounds, list): bounds = tuple(bounds)

        def calculate_score(candidate):
            try:
                base_vector = np.array([
                    float(candidate.get("kcal", 0)),
                    float(candidate.get("protein", 0)),
                    float(candidate.get("totalfat", 0)),
                    float(candidate.get("carbs", 0))
                ])
                if np.sum(base_vector) == 0: return float('inf'), 1.0

                def objective(x):
                    current_vector = base_vector * x
                    diff = (current_vector - target_vector) / (target_vector + 1e-5)
                    loss = np.sum(weights * (diff ** 2))
                    return loss

                res = minimize_scalar(objective, bounds=bounds, method='bounded')
                if res.success:
                    return res.fun, res.x
                return float('inf'), 1.0
            except:
                return float('inf'), 1.0

        scored_candidates = []
        for item in candidates:
            loss, scale = calculate_score(item)
            item_score = item.copy()
            item_score["optimization_loss"] = round(loss, 4)
            item_score["portion_scale"] = round(scale, 2)
            item_score["final_kcal"] = int(item["kcal"] * scale)
            item_score["final_protein"] = int(item["protein"] * scale)
            item_score["final_totalfat"] = int(item["totalfat"] * scale)
            item_score["final_carbs"] = int(item["carbs"] * scale)
            scored_candidates.append(item_score)
            
        scored_candidates.sort(key=lambda x: x["optimization_loss"])
        top_10 = scored_candidates[:10]

        logger.info(f"📊 Scipy đã lọc ra {len(top_10)} ứng viên tiềm năng.")
        for item in top_10:
            logger.info(f"   - {item['name']} (Scale x{item['portion_scale']} | Loss: {item['optimization_loss']})")

        return {"top_candidates": top_10}

    async def node_select_meal(self, state: SwapState):
        logger.info("---NODE: SELECT MEAL---")
        top_candidates = state.get("top_candidates", [])
        food_old = state.get("food_old")
        
        if not top_candidates: return {"best_replacement": None}
        
        options_text = ""
        for item in top_candidates:
            options_text += (
                f"ID [{item.get('meal_id')}] - {item['name']}\n"
                f"   - Stats: {item['final_kcal']} Kcal | P:{item['final_protein']}g\n"
            )
            
        system_prompt = f"""
        Bạn là Bếp trưởng. Người dùng muốn đổi món '{food_old.get('name')}'.
        Dưới đây là các ứng viên thay thế:
        {options_text}
        NHIỆM VỤ:
        1. Chọn ra 1 món thay thế tốt nhất về mặt ẩm thực.
        2. Trả về chính xác ID (số trong ngoặc vuông []) của món đó.
        """
        
        try:
            llm_structured = self.llm.with_structured_output(ChefDecision)
            time_start = time.time()
            decision = await llm_structured.ainvoke(system_prompt)
            time_end = time.time()
            logger.info(f"🤖 Thời gian chọn món: {time_end - time_start:.2f} giây")
            target_id = decision.selected_meal_id
        except Exception as e:
            logger.info(f"⚠️ Lỗi LLM: {e}. Fallback về option đầu tiên.")
            # Fallback lấy ID của món đầu tiên
            target_id = top_candidates[0].get("meal_id")
            decision = ChefDecision(selected_meal_id=target_id, reason="Fallback do lỗi hệ thống.")
             
        selected_full_candidate = None

        for item in top_candidates:
            if int(item.get("meal_id")) == int(target_id):
                selected_full_candidate = item
                break

        # Fallback an toàn
        if not selected_full_candidate:
            logger.info(f"⚠️ ID {target_id} không tồn tại trong list. Chọn món Top 1.")
            selected_full_candidate = top_candidates[0]

        # Bổ sung lý do
        selected_full_candidate["chef_reason"] = decision.reason

        #-------------------------------------------------------------------
        # --- PHẦN MỚI: IN BẢNG SO SÁNH (VISUAL COMPARISON) ---
        logger.info(f"✅ CHEF SELECTED: {selected_full_candidate['name']} (ID: {selected_full_candidate['meal_id']})")
        logger.info(f"📝 Lý do: {decision.reason}")

        # Lấy thông tin món cũ (đã scale ở menu gốc)
        old_kcal = float(food_old.get('final_kcal', food_old['kcal']))
        old_pro = float(food_old.get('final_protein', food_old['protein']))
        old_fat = float(food_old.get('final_totalfat', food_old['totalfat']))
        old_carb = float(food_old.get('final_carbs', food_old['carbs']))

        # Lấy thông tin món mới (đã re-scale bởi Scipy)
        new_kcal = selected_full_candidate['final_kcal']
        new_pro = selected_full_candidate['final_protein']
        new_fat = selected_full_candidate['final_totalfat']
        new_carb = selected_full_candidate['final_carbs']
        scale = selected_full_candidate['portion_scale']

        # In bảng
        logger.info("\n   📊 BẢNG SO SÁNH THAY THẾ:")
        headers = ["Chỉ số", "Món Cũ (Gốc)", "Món Mới (Re-scale)", "Chênh lệch"]
        row_fmt = "   | {:<10} | {:<15} | {:<20} | {:<12} |"

        logger.info("   " + "-"*68)
        logger.info(row_fmt.format(*headers))
        logger.info("   " + "-"*68)

        def print_row(label, old_val, new_val, unit=""):
            diff = new_val - old_val
            diff_str = f"{diff:+.1f}"

            # Đánh dấu màu (Logic text)
            status = "✅"
            # Nếu lệch > 20% thì cảnh báo
            if old_val > 0 and abs(diff)/old_val > 0.2: status = "⚠️"

            logger.info(row_fmt.format(
                label,
                f"{old_val:.0f} {unit}",
                f"{new_val:.0f} {unit} (x{scale} suất)",
                f"{diff_str} {status}"
            ))

        print_row("Năng lượng", old_kcal, new_kcal, "Kcal")
        print_row("Protein", old_pro, new_pro, "g")
        print_row("TotalFat", old_fat, new_fat, "g")
        print_row("Carb", old_carb, new_carb, "g")
        logger.info("   " + "-"*68)

        logger.info(f"✅ Chef Selected: ID {selected_full_candidate['meal_id']} - {selected_full_candidate['name']}")
        
        return {"best_replacement": selected_full_candidate}
