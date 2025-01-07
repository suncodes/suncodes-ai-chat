"""
常量
"""
from suncodes_ai_chat.suncodes_config.config_manager import config_manager

TEMPERATURE = 0.1
DEEPSEEK_MODEL = "deepseek-chat"
DEEPSEEK_API_KEY = config_manager.get_value('DEEPSEEK_API_KEY')
DEEPSEEK_BASE_URL = "https://api.deepseek.com/v1"
