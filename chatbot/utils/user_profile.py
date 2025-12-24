import logging
import requests
from chatbot.config import API_BASE_URL

# --- Cấu hình logging ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- User profile ---
def get_user_by_id(user_id: int):
    url = f"{API_BASE_URL}/get_all_info?id={user_id}"

    user_profile = {'id': 1, 'fullname': 'An', 'age': 22, 'height': 12, 'weight': 42, 'activityLevel': 'Ít vận động', 'limitFood': 'Dị ứng sữa, Thuần chay','healthStatus': 'Không có', 'diet': 'Chế độ HighProtein', 'bmr': 583.73, 'tdee': 700.476, 'gender': 'male',
        'userinfoid': 1, 'targetcalories': 1033.8093, 'water': 1260.0, 'protein': 90.45831, 'totalfat': 22.973541, 'saturatedfat': 8.040739, 'monounsaturatedfat': 10.338094, 'polyunsaturatedfat': 4.594708, 'transfat': 0.0,
        'carbohydrate': 116.30355, 'carbs': 90.71677, 'sugar': 8.141249, 'fiber': 17.445532, 'cholesterol': 300.0, 'vitamina': 3000.0, 'vitamind': 15.0, 'vitaminc': 90.0, 'vitaminb6': 1.3, 'vitaminb12': 2.4, 'vitamine': 15.0,
        'vitamink': 120.0, 'choline': 550.0, 'canxi': 1000.0, 'fe': 8.0, 'magie': 400.0, 'photpho': 700.0, 'kali': 4700.0, 'natri': 2300.0, 'zn': 11.0, 'caffeine': 126.0, 'alcohol': 20.0
    }

    try:
        response = requests.get(url, timeout=3)
        response.raise_for_status()

        result = response.json()
        userInfo = result['userInfo']
        requiredIndex = result['requiredIndex']
        user_profile = {**userInfo, **requiredIndex}
        
        logger.info(f"Lấy profile cho user_id={user_id} tên {user_profile['fullname']}")
        
        return user_profile

    except requests.HTTPError as http_err:
        logger.warning(f"HTTP error occurred: {http_err}")
    except Exception as e:
        logger.warning(f"Other error: {e}")

    logger.info(f"Sử dụng profile mặc định cho user_id={user_id}")
    
    return user_profile