import logging
from typing import Dict, Any

# --- Cấu hình logging ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- User profile ---
def get_user_by_id(user_id: str) -> Dict[str, Any]:
    """
    Lấy thông tin người dùng từ DB hoặc hệ thống.
    Nếu không tìm thấy, trả về default.
    """
    if not user_id:
        logger.warning("User ID trống, sử dụng profile mặc định")
        return {}

    # Thử lấy từ DB (ở đây tạm hardcode)
    user_profile = {
        "kcal": 1700,
        "protein": 120,
        "lipid": 56,
        "carbohydrate": 170,
        "khẩu phần": "ăn chay"
    }
    logger.info(f"Lấy profile cho user_id={user_id}: {user_profile}")
    return user_profile