import logging
from urllib.parse import quote_plus, urlencode

import requests

from suncodes_ai_chat.suncodes_common.oss.oss_cli import CustomOSSClient
from suncodes_ai_chat.suncodes_constants import baidu_constants
from suncodes_ai_chat.suncodes_utils.file_base64 import get_mp3_duration


class BaiduTTSBase:
    def __init__(self, **kwargs):
        self.api_key = baidu_constants.ASR_TTS_API_KEY
        self.api_secret = baidu_constants.ASR_TTS_SECRET_KEY
        self.api_url = baidu_constants.TTS_API_URL
        self.token_url = baidu_constants.ASR_TTS_ACCESS_TOKEN_URL
        self.cuid = baidu_constants.ASR_TTS_CUID
        # 音色
        self.voice = kwargs.get("voice", 4)
        # 语速
        self.rate = kwargs.get("rate", 5)
        # 音量
        self.volume = kwargs.get("volume", 5)
        self.audio_format = kwargs.get("audio_format", "mp3")
        self.audio_format_mapping = {
            'pcm': 4,
            'mp3': 3,
            'wav': 6,
        }

    def get_access_token(self):
        """
        使用 AK，SK 生成鉴权签名（Access Token）
        :return: access_token，或是None(如果错误)
        """
        url = self.token_url
        params = {"grant_type": "client_credentials", "client_id": self.api_key, "client_secret": self.api_secret}
        return str(requests.post(url, params=params).json().get("access_token"))

    def tts_by_baidu(self, text : str, params: dict = None):
        """
        text: 文本
        per： 音色，度小宇=1，度小美=0，度逍遥（基础）=3，度丫丫=4，详情：https://ai.baidu.com/ai-doc/SPEECH/mlbxh7xie
        spd：语速，取值0-15，默认为5中语速
        pit：音调，取值0-15，默认为5中语调
        vol：音量，基础音库取值0-9，精品音库取值0-15，默认为5中音量（取值为0时为音量最小值，并非为无声）
        aue：音频格式，3为mp3格式(默认)；
            4为pcm-16k；5为pcm-8k；
            6为wav（内容同pcm-16k）;
            注意aue=4或者6是语音识别要求的格式，但是音频内容不是语音识别要求的自然人发音，所以识别效果会受影响。
        """
        url = self.api_url
        if params is None:
            params = {}
        per = params.get("voice", self.voice)
        spd = params.get("rate", self.rate)
        pit = 5
        vol = params.get("volume", self.volume)
        # TODO 目前只支持MP3
        aue = self.audio_format_mapping.get(params.get("audio_format", self.audio_format), 3)

        token = self.get_access_token()
        # 此处TEXT需要两次urlencode
        tex = quote_plus(text)
        logging.info(tex)
        params = {'tok': token, 'tex': tex, 'per': per,
                  'spd': spd, 'pit': pit, 'vol': vol, 'aue': aue, 'cuid': self.cuid,
                  'lan': 'zh', 'ctp': 1}  # lan ctp 固定参数

        payload = urlencode(params)
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Accept': '*/*'
        }
        response = requests.request("POST", url, headers=headers, data=payload)
        content = response.content
        logging.info(f"百度text2audio 响应码：{response.status_code}, 响应头：{response.headers}")
        content_type = response.headers.get('Content-Type', None)

        if content_type is not None and content_type.find('audio/') != -1:
            # 将 bytes
            oss = CustomOSSClient()
            return oss.upload_file_random_path(content), get_mp3_duration(content)
        else:
            return None, 0

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    tts = BaiduTTSBase()
    print(tts.tts_by_baidu("你好", {
            "voice": 4,
            "rate": 5,
            "pit": 5,
            "volume": 5,
            "audio_format": 'mp3'
        }))
