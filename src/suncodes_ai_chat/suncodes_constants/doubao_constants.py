from suncodes_ai_chat.suncodes_config.config_manager import config_manager

TEMPERATURE = 0.1
DOUBAO_MODEL = "ep-20241210201346-d8fsz"
DOUBAO_BASE_URL = "https://ark.cn-beijing.volces.com/api/v3"
DOUBAO_API_KEY = config_manager.get_value('DOUBAO_API_KEY')
