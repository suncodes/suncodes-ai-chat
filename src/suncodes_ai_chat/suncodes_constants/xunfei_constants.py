from suncodes_ai_chat.suncodes_config.config_manager import config_manager

API_KEY = config_manager.get_value("XUNFEI_API_KEY")
SECRET_KEY = config_manager.get_value("XUNFEI_SECRET_KEY")
APP_ID = config_manager.get_value("XUNFEI_APP_ID")
ASR_API_URL = "wss://iat.cn-huabei-1.xf-yun.com/v1"
ASR_ZH_API_URL = "wss://iat.xf-yun.com/v1"
TTS_API_URL = "wss://cbm01.cn-huabei-1.xf-yun.com/v1/private/mcd9m97e6"
ISE_API_URL = "ws://ise-api.xfyun.cn/v2/open-ise"
