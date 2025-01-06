import json
import logging

import requests

from suncodes_ai_chat.suncodes_constants import baidu_constants
from suncodes_ai_chat.suncodes_utils.file_base64 import get_file_size_from_base64


class BaiduASRBase:
    """
    支持wav文件
    """
    def __init__(self):
        self.api_key = baidu_constants.ASR_TTS_API_KEY
        self.api_secret = baidu_constants.ASR_TTS_SECRET_KEY
        self.api_url = baidu_constants.ASR_API_URL
        self.token_url = baidu_constants.ASR_TTS_ACCESS_TOKEN_URL
        self.cuid = baidu_constants.ASR_TTS_CUID

    def get_access_token(self):
        """
        使用 AK，SK 生成鉴权签名（Access Token）
        :return: access_token，或是None(如果错误)
        """
        url = self.token_url
        params = {"grant_type": "client_credentials", "client_id": self.api_key, "client_secret": self.api_secret}
        return str(requests.post(url, params=params).json().get("access_token"))

    def asr_by_baidu(self, content_base64) -> dict:
        """
        百度语音转文字，文件格式 wav
        """
        url = self.api_url
        # 使用函数
        file_size = get_file_size_from_base64(content_base64)

        payload = json.dumps({
            "format": "wav",
            "rate": 16000,
            # 默认 1537（普通话 输入法模型）
            # 1737	英语
            "dev_pid": 1737,
            "channel": 1,
            "cuid": self.cuid,
            "speech": content_base64,
            "len": file_size,
            "token": self.get_access_token()
        })
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        response = requests.request("POST", url, headers=headers, data=payload)
        logging.info(response.text)
        # 注意 success 后面有个点.
        # 正常 {"corpus_no":"6433214037620997779","err_msg":"success.","err_no":0,"result":["北京科技馆，"],
        # "sn":"371191073711497849365"}
        # 错误 {"err_msg":"invalid audio length","err_no":3314,"sn":"661202272311730942197"}
        return response.json()
