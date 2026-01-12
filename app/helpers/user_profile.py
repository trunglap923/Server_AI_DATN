import logging
import requests
from app.core.config import settings

# --- Cấu hình logging ---
logger = logging.getLogger(__name__)

# --- User profile ---
def get_user_by_id(user_id: int):
    url = f"{settings.API_BASE_URL}/get_all_info?id={user_id}"

    user_profile = {'id': 1, 'fullname': 'Default User', 'age': 25, 'height': 170, 'weight': 60, 'activityLevel': 'Vừa phải', 'limitFood': 'Không có','healthStatus': 'Không có', 'diet': 'Cân bằng', 'bmr': 1500, 'tdee': 2000, 'gender': 'male',
        'userinfoid': 1, 'targetcalories': 2000, 
    }

    try:
        response = requests.get(url, timeout=3)
        response.raise_for_status()

        result = response.json()
        userInfo = result.get('userInfo', {})
        requiredIndex = result.get('requiredIndex', {})
        user_profile = {**userInfo, **requiredIndex}
        
        logger.info(f"Lấy profile cho user_id={user_id} tên {user_profile.get('fullname', 'Unknown')}")
        
        return user_profile

    except requests.HTTPError as http_err:
        logger.warning(f"HTTP error occurred: {http_err}")
    except Exception as e:
        logger.warning(f"Other error: {e}")

    logger.info(f"Sử dụng profile mặc định cho user_id={user_id}")
    
    return user_profile
