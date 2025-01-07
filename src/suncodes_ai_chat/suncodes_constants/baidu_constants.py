from suncodes_ai_chat.suncodes_config.config_manager import config_manager

ASR_TTS_API_KEY = config_manager.get_value("BAIDU_API_LEY")
ASR_TTS_SECRET_KEY = config_manager.get_value("BAIDU_SECRET_KEY")
# uv 统计使用，
ASR_TTS_CUID = "suncodes_ai_help"
ASR_TTS_ACCESS_TOKEN_URL = "https://aip.baidubce.com/oauth/2.0/token"
ASR_API_URL = "https://vop.baidu.com/server_api"
TTS_API_URL = "https://tsn.baidu.com/text2audio"
