from dotenv import load_dotenv
import os

load_dotenv()

DEEPSEEK_API_KEY = os.getenv('DEEPSEEK_API_KEY')

ELASTIC_CLOUD_URL = os.getenv('ELASTIC_CLOUD_URL')
ELASTIC_API_KEY = os.getenv('ELASTIC_API_KEY')
FOOD_DB_INDEX = os.getenv('FOOD_DB_INDEX')
POLICY_DB_INDEX = os.getenv('POLICY_DB_INDEX')

API_BASE_URL=os.getenv('API_BASE_URL')
