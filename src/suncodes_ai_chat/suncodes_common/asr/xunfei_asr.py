# -*- coding:utf-8 -*-
#
#   author: iflytek
#
#  本demo测试时运行的环境为：Windows + Python3.7
#  本demo测试成功运行时所安装的第三方库及其版本如下，您可自行逐一或者复制到一个新的txt文件利用pip一次性安装：
#   cffi==1.12.3
#   gevent==1.4.0
#   greenlet==0.4.15
#   pycparser==2.19
#   six==1.12.0
#   websocket==0.2.1
#   websocket-client==0.56.0
#
#  语音听写流式 WebAPI 接口调用示例 接口文档（必看）：https://doc.xfyun.cn/rest_api/语音听写（流式版）.html
#  webapi 听写服务参考帖子（必看）：http://bbs.xfyun.cn/forum.php?mod=viewthread&tid=38947&extra=
#  语音听写流式WebAPI 服务，热词使用方式：登陆开放平台https://www.xfyun.cn/后，找到控制台--我的应用---语音听写（流式）---服务管理--个性化热词，
#  设置热词
#  注意：热词只能在识别的时候会增加热词的识别权重，需要注意的是增加相应词条的识别率，但并不是绝对的，具体效果以您测试为准。
#  语音听写流式WebAPI 服务，方言试用方法：登陆开放平台https://www.xfyun.cn/后，找到控制台--我的应用---语音听写（流式）---服务管理--识别语种列表
#  可添加语种或方言，添加后会显示该方言的参数值
#  错误码链接：https://www.xfyun.cn/document/error-code （code返回错误码时必看）
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
import _thread as thread
import asyncio
import base64
import datetime
import hashlib
import hmac
import json
import logging
import time
from datetime import datetime
from time import mktime
from urllib.parse import urlencode
from wsgiref.handlers import format_date_time

import websockets

from suncodes_ai_chat.suncodes_constants import xunfei_constants
from suncodes_ai_chat.suncodes_common.tts.xunfei_tts import get_authorization_url

STATUS_FIRST_FRAME = 0  # 第一帧的标识
STATUS_CONTINUE_FRAME = 1  # 中间帧标识
STATUS_LAST_FRAME = 2  # 最后一帧的标识


class XunfeiASRBase:
    """
    讯飞语音转文字，支持pcm和MP3两种格式的文件
    """

    def __init__(self, **kwargs):
        self.language = kwargs.get("language", "en")
        self.api_key = xunfei_constants.API_KEY
        self.api_secret = xunfei_constants.SECRET_KEY
        if self.language == "zh":
            self.api_url = xunfei_constants.ASR_ZH_API_URL
        else:
            self.api_url = xunfei_constants.ASR_API_URL
        self.appid = xunfei_constants.APP_ID
        self.audio_format_mapping = {
            'pcm': "raw",
            'mp3': "lame",
        }

    async def asr_by_xunfei(self, content_base64, file_suffix_no_dot="mp3"):
        """
        asr识别
        :param content_base64:
        :param file_suffix_no_dot:
        :return:
        """
        ws_url = get_authorization_url(self.api_url, self.api_key, self.api_secret)
        result = "语音转文字失败"
        try:
            result = await self.request_wss(url=ws_url,
                                            base64_data=content_base64,
                                            file_suffix_no_dot=file_suffix_no_dot)
            logging.info("科大讯飞识别结果：%s", result)
        except Exception as e:
            print(f"捕获到异常: {e}")
            logging.exception(e)
        return result

    async def request_wss(self, url, base64_data, file_suffix_no_dot):
        # 将 base64 数据解码为原始字节流
        audio_data = base64.b64decode(base64_data)

        async with websockets.connect(url) as websocket:
            frame_size = 1280  # 每一帧的音频大小
            intervel = 0.04  # 发送音频间隔(单位:s)
            frame_end_flag = False
            status_frame = STATUS_FIRST_FRAME  # 音频的状态信息，标识音频是第一帧，还是中间帧、最后一帧

            data_length = len(audio_data)
            offset = 0
            while not frame_end_flag:
                buf = None
                if offset >= data_length:
                    status_frame = STATUS_LAST_FRAME
                else:
                    # 读取当前帧的字节数据
                    # 取 data_length 和 offset + frame_size 较小值
                    min_size = min(data_length, offset + frame_size)
                    buf = audio_data[offset:min_size]
                    # 更新偏移量
                    offset += frame_size
                if not buf:
                    audio = None
                else:
                    audio = str(base64.b64encode(buf), 'utf-8')

                message = self.build_send_message(file_suffix_no_dot, audio, status_frame)
                await websocket.send(message)
                if status_frame == STATUS_FIRST_FRAME:
                    status_frame = STATUS_CONTINUE_FRAME
                if status_frame == STATUS_LAST_FRAME:
                    frame_end_flag = True
                # 模拟音频采样间隔
                time.sleep(intervel)

            result = ""
            status = -1
            while status != 2:
                if status == 0:
                    result = "语音转文字失败"
                    break
                response = await websocket.recv()
                # 响应数据处理
                response_json = self.get_response_json(response)
                status = response_json["status"]
                result += response_json["text"]

            await websocket.close()
            return result

    def build_send_message(self, file_suffix_no_dot, audio, status_frame):
        iat_param = {
            "domain": "slm",
            "accent": "mandarin",
            "result":
                {
                    "encoding": "utf8",
                    "compress": "raw",
                    "format": "json"
                }
        }
        if self.language == 'zh':
            iat_param['language'] = "zh_cn"
        else:
            iat_param['language'] = "mul_cn"
            iat_param['ln'] = "en"

        if status_frame == STATUS_FIRST_FRAME:
            d = {"header":
                {
                    "status": 0,
                    "app_id": self.appid
                },
                "parameter": {
                    "iat": iat_param
                },
                "payload": {
                    "audio":
                        {
                            "audio": audio,
                            "sample_rate": 16000,
                            "encoding": self.audio_format_mapping[file_suffix_no_dot]
                        }
                }}
            return json.dumps(d)

        if status_frame == STATUS_CONTINUE_FRAME:
            d = {"header": {"status": 1,
                            "app_id": self.appid},
                 "payload": {
                     "audio":
                         {
                             "audio": audio,
                             "sample_rate": 16000,
                             "encoding": self.audio_format_mapping[file_suffix_no_dot]
                         }}}
            return json.dumps(d)

        if status_frame == STATUS_LAST_FRAME:
            d = {"header": {"status": 2,
                            "app_id": self.appid
                            },
                 "payload": {
                     "audio":
                         {
                             "audio": audio,
                             "sample_rate": 16000,
                             "encoding": self.audio_format_mapping[file_suffix_no_dot]
                         }}}
            return json.dumps(d)

    @staticmethod
    def get_response_json(message):
        """
        格式化返回值
        :param message:
        :return:
        """
        message = json.loads(message)
        code = message["header"]["code"]
        status = message["header"]["status"]

        return_json = {"status": 0, "text": ""}

        if code != 0:
            logging.error("请求错误：%s", code)
        else:
            return_json["status"] = 1
            payload = message.get("payload")
            if payload:
                text = payload["result"]["text"]
                text = json.loads(str(base64.b64decode(text), "utf8"))
                text_ws = text['ws']
                result = ''
                for i in text_ws:
                    for j in i["cw"]:
                        w = j["w"]
                        result += w
                return_json["text"] = result
            if status == 2:
                return_json["status"] = 2
        logging.info("wss---response %s", json.dumps(return_json))
        return return_json
