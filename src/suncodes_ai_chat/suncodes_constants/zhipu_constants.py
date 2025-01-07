from suncodes_ai_chat.suncodes_config.config_manager import config_manager

TEMPERATURE = 0.1
MODEL = "glm-4-plus"
EMBEDDINGS_MODEL = "embedding-3"
OPENAI_API_BASE = "https://open.bigmodel.cn/api/paas/v4/"
OPENAI_API_KEY = config_manager.get_value('ZHIPU_API_KEY')
