import logging
import numpy as np
from scipy.optimize import minimize
from typing import List, Dict, Any

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OptimizationService:
    def optimize_menu(self, user_profile: Dict[str, Any], menu: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        logger.info("---SERVICE: OPTIMIZATION STARTED---")
        
        if not menu:
            logger.warning("⚠️ Menu empty, skipping optimization.")
            return []

        # --- STEP 1: DEFINE TARGETS ---
        daily_targets = np.array([
            float(user_profile.get("targetcalories", 1314)),
            float(user_profile.get("protein", 98)),
            float(user_profile.get("totalfat", 43)),
            float(user_profile.get("carbohydrate", 131))
        ])

        meal_ratios = {"sáng": 0.25, "trưa": 0.40, "tối": 0.35}
        generated_meals = set(d.get("assigned_meal", "").lower() for d in menu)

        # Tính Target Thực Tế (Optimization Target)
        # Ví dụ: Nếu chỉ có bữa Trưa -> Target = Daily * 0.4
        # Nếu có Trưa + Tối -> Target = Daily * (0.4 + 0.35)
        active_target = np.zeros(4)
        active_ratios_sum = 0

        for m in ["sáng", "trưa", "tối"]:
            if m in generated_meals:
                active_target += daily_targets * meal_ratios[m]
                active_ratios_sum += meal_ratios[m]

        if np.sum(active_target) == 0:
            active_target = daily_targets

        logger.info(f"   🎯 Optimization Target (Active): {active_target.astype(int)}")

        # --- STEP 2: SETUP MATRIX & BOUNDS ---
        matrix = []
        bounds = []
        meal_indices = {"sáng": [], "trưa": [], "tối": []}

        target_kcal_per_meal = {
            k: daily_targets[0] * v for k, v in meal_ratios.items()
        }

        for i, dish in enumerate(menu):
            nutrients = [
                float(dish.get("kcal", 0)),
                float(dish.get("protein", 0)),
                float(dish.get("totalfat", 0)),
                float(dish.get("carbs", 0))
            ]
            matrix.append(nutrients)

            current_kcal = nutrients[0]
            t_meal_name = dish.get("assigned_meal", "").lower()
            t_meal_target = target_kcal_per_meal.get(t_meal_name, 500)

            if current_kcal > (t_meal_target * 0.9):
                 bounds.append((0.3, 1.0))
            elif "solver_bounds" in dish:
                bounds.append(dish["solver_bounds"])
            else:
                bounds.append((0.5, 1.5))

            if "sáng" in t_meal_name: meal_indices["sáng"].append(i)
            elif "trưa" in t_meal_name: meal_indices["trưa"].append(i)
            elif "tối" in t_meal_name: meal_indices["tối"].append(i)

        matrix = np.array(matrix).T
        n_dishes = len(menu)
        initial_guess = np.ones(n_dishes)

        # --- STEP 3: ADAPTIVE WEIGHTS ---
        optimized_portions = initial_guess
        try:
            max_possible = matrix.dot(np.full(n_dishes, 2.5))
            adaptive_weights = np.array([3.0, 2.0, 1.0, 1.0])
            nutri_names = ["Kcal", "Protein", "Lipid", "Carb"]

            for i in range(1, 4):
                if max_possible[i] < (active_target[i] * 0.7):
                    logger.info(f"   ⚠️ Severe shortage of {nutri_names[i]}. Reducing weight.")
                    adaptive_weights[i] = 0.01

            # --- STEP 4: LOSS FUNCTION ---
            def objective(portions):
                # A. Macro Loss
                current_macros = matrix.dot(portions)
                diff = (current_macros - active_target) / (active_target + 1e-5)
                loss_macro = np.sum(adaptive_weights * (diff ** 2))

                # B. Distribution Loss
                loss_dist = 0
                if active_ratios_sum > 0.5:
                    kcal_row = matrix[0]
                    for m_type, indices in meal_indices.items():
                        if not indices: continue
                        current_meal_kcal = np.sum(kcal_row[indices] * portions[indices])
                        target_meal = target_kcal_per_meal.get(m_type, 0)
                        d = (current_meal_kcal - target_meal) / (target_meal + 1e-5)
                        loss_dist += (d ** 2)

                return 2 * loss_macro + loss_dist

            # 5. Run Optimization
            res = minimize(objective, initial_guess, method='SLSQP', bounds=bounds)
            
            if res.success:
                optimized_portions = res.x
            else:
                logger.warning(f"⚠️ Solver failed: {res.message}. Using default portions.")
                
        except Exception as e:
            logger.error(f"🔥 SOLVER ERROR: {e}")
            optimized_portions = np.ones(n_dishes)

        # 6. Apply Results
        final_menu = []

        total_stats = np.zeros(4)
        achieved_meal_kcal = {"sáng": 0, "trưa": 0, "tối": 0}

        for i, dish in enumerate(menu):
            ratio = optimized_portions[i]
            final_dish = dish.copy()

            final_dish["portion_scale"] = float(round(ratio, 2))
            final_dish["final_kcal"] = int(dish.get("kcal", 0) * ratio)
            final_dish["final_protein"] = int(dish.get("protein", 0) * ratio)
            final_dish["final_totalfat"] = int(dish.get("totalfat", 0) * ratio)
            final_dish["final_carbs"] = int(dish.get("carbs", 0) * ratio)

            logger.info(f"   - {dish['name']} ({dish['assigned_meal']}): x{final_dish['portion_scale']} suất -> {final_dish['final_kcal']}kcal, {final_dish['final_protein']}g Protein, {final_dish['final_totalfat']}g Total Fat, {final_dish['final_carbs']}g Carbs")

            final_menu.append(final_dish)
            total_stats += np.array([
                final_dish["final_kcal"], final_dish["final_protein"],
                final_dish["final_totalfat"], final_dish["final_carbs"]
            ])

            m_type = dish.get("assigned_meal", "").lower()
            if "sáng" in m_type: achieved_meal_kcal["sáng"] += final_dish["final_kcal"]
            elif "trưa" in m_type: achieved_meal_kcal["trưa"] += final_dish["final_kcal"]
            elif "tối" in m_type: achieved_meal_kcal["tối"] += final_dish["final_kcal"]

        logger.info("\n   📊 BÁO CÁO TỐI ƯU HÓA CHI TIẾT:")
        headers = ["Chỉ số", "Mục tiêu (Bữa)", "Kết quả", "Độ lệch"]
        row_format = "   | {:<12} | {:<15} | {:<15} | {:<15} |"
        logger.info("   " + "-"*65)
        logger.info(row_format.format(*headers))
        logger.info("   " + "-"*65)

        labels = ["Năng lượng", "Protein", "TotalFat", "Carb"]
        units = ["Kcal", "g", "g", "g"]

        for i in range(4):
            t_val = int(active_target[i]) # So sánh với Active Target
            r_val = int(total_stats[i])
            diff = r_val - t_val
            diff_str = f"{diff:+d} {units[i]}"

            status = ""
            percent_diff = abs(diff) / (t_val + 1e-5)
            # Nếu weight bị giảm về 0.01 thì không cảnh báo lỗi nữa (vì đã chấp nhận bỏ qua)
            if percent_diff > 0.15 and adaptive_weights[i] > 0.1: status = "⚠️"
            else: status = "✅"

            logger.info(row_format.format(
                labels[i],
                f"{t_val} {units[i]}",
                f"{r_val} {units[i]}",
                f"{diff_str} {status}"
            ))
        logger.info("   " + "-"*65)

        logger.info("\n   ⚖️  PHÂN BỔ TỪNG BỮA (Kcal):")
        for meal in ["sáng", "trưa", "tối"]:
            if meal in generated_meals:
                t_meal = int(target_kcal_per_meal[meal])
                r_meal = int(achieved_meal_kcal[meal])
                logger.info(f"   - {meal.capitalize():<5}: Đạt {r_meal} / {t_meal} Kcal")

        return final_menu
