import base64
import datetime
import hashlib
import hmac
import json
import logging
import ssl
import time
from datetime import datetime
from time import sleep
from urllib.parse import urlencode
from wsgiref.handlers import format_date_time

import websocket
import websockets

from suncodes_ai_chat.suncodes_common.base_stream.queue_manager import QueueManager
from suncodes_ai_chat.suncodes_common.oss.oss_cli import CustomOSSClient
from suncodes_ai_chat.suncodes_constants import xunfei_constants
from suncodes_ai_chat.suncodes_utils.file_base64 import get_mp3_duration

logging = logging.getLogger(__name__)

class XunfeiTTSBase:
    """
    支持 输出 pcm 和 mp3
    """

    def __init__(self, **kwargs):
        # 音色
        self.voice = kwargs.get("voice", "x4_lingxiaoxuan_oral")
        # 语速
        self.rate = kwargs.get("rate", 50)
        # 音量
        self.volume = kwargs.get("volume", 50)
        self.audio_format = kwargs.get("audio_format", "mp3")
        self.api_key = xunfei_constants.API_KEY
        self.api_secret = xunfei_constants.SECRET_KEY
        self.api_url = xunfei_constants.TTS_API_URL
        self.appid = xunfei_constants.APP_ID
        self.audio_format_mapping = {
            'pcm': "raw",
            'mp3': "lame",
        }
        self.s3_client = CustomOSSClient()


    async def tts_by_xunfei(self, text, params: dict = None):
        """
        text: 待合成的文本
        params：需要设置的参数
        详见初始化方法中的默认值
        """
        logging.info("tts_by_xunfei 开始合成：" + text)
        ws_url = get_authorization_url(self.api_url, self.api_key, self.api_secret)
        param = self.__init_send_param(text, params)
        speech_url = ""
        duration = 0
        try:
            result = await self.request_wss(ws_url=ws_url, param=param)
            if result is not None:
                # 保存到 s3 中
                speech_url = self.s3_client.upload_file_random_path(result)
                # TODO 目前只支持MP3
                duration = get_mp3_duration(result)
            logging.info("tts_by_xunfei 科大讯飞识别结果：%s", speech_url)
        except Exception as e:
            print(f"捕获到异常: {e}")
            logging.exception(e)
        return speech_url, duration

    async def request_wss(self, ws_url, param):
        async with websockets.connect(ws_url) as websocket:
            await websocket.send(param)
            combined_data = bytearray()
            status = -2
            final_flag = True
            while status != 2:
                if status == -1:
                    final_flag = False
                    break
                response = await websocket.recv()
                # 响应数据处理
                response_json = self.get_response_json(response)
                status = response_json["status"]
                combined_data.extend(base64.b64decode(response_json["audio"]))
            await websocket.close()
            # 最终得到所有文件合并后的字节流
            result = bytes(combined_data)
            if final_flag:
                return result
            return None

    @staticmethod
    def get_response_json(message):
        # 0:开始, 1:中间, 2:结束(一次性合成直接传2)
        return_json = {"status": 0, "audio": ""}

        message = json.loads(message)
        code = message["header"]["code"]
        sid = message["header"]["sid"]
        if code != 0:
            errMsg = message["message"]
            logging.error("sid:%s call error:%s code is:%s", sid, errMsg, code)
            return_json["status"] = -1
        else:
            if "payload" in message:
                audio = message["payload"]["audio"]['audio']
                # audio = base64.b64decode(audio)
                status = message["payload"]['audio']["status"]
                return_json["status"] = 1
                # base64
                return_json["audio"] = audio
                if status == 2:
                    logging.info("ws is closed")
                    return_json["status"] = 2
        logging.info("wss---response" + json.dumps(return_json))
        return return_json

    def __init_send_param(self, text, params: dict) -> str:
        data_copy = {
            "text": {
                "encoding": "utf8",
                "compress": "raw",
                "format": "plain",
                "status": 2,
                "seq": 0,
                "text": str(base64.b64encode(text.encode('utf-8')), "UTF8")
            }
        }
        if params is None:
            params = {}

        d = {"header": {"app_id": self.appid, "status": 2},
             "parameter": {
                 "tts": {
                     # 音色
                     "vcn": params.get("voice", self.voice),  # 发音人参数，更换不同的发音人会有不同的音色效果
                     "volume": params.get("volume", self.volume),  # 设置音量大小
                     "rhy": 0,  # 是否返回拼音标注		0:不返回拼音, 1:返回拼音（纯文本格式，utf8编码）
                     "speed": params.get("rate", self.rate),  # 设置合成语速，值越大，语速越快
                     "pitch": 50,  # 设置振幅高低，可通过该参数调整效果
                     "bgs": 0,  # 背景音	0:无背景音, 1:内置背景音1, 2:内置背景音2
                     "reg": 0,  # 英文发音方式 	0:自动判断处理，如果不确定将按照英文词语拼写处理（缺省）,
                     # 1:所有英文按字母发音, 2:自动判断处理，如果不确定将按照字母朗读
                     "rdn": 0,  # 合成音频数字发音方式	0:自动判断, 1:完全数值, 2:完全字符串, 3:字符串优先
                     "audio": {
                         # 合成音频格式， lame 合成音频格式为mp3
                         "encoding": self.audio_format_mapping[params.get("audio_format", self.audio_format)],
                         "sample_rate": 16000,  # 合成音频采样率，	16000, 8000, 24000
                         "channels": 1,  # 音频声道数
                         "bit_depth": 16,  # 合成音频位深 ：16, 8
                         "frame_size": 0
                     }
                 }
             },
             "payload": data_copy,
             }
        d = json.dumps(d)
        return d


class XunfeiTTSStream:
    def __init__(self, queue_manager: QueueManager, **kwargs):
        self.queue_manager = queue_manager
        # 发送时所需的参数：发送顺序
        self.send_seqs = {}
        # 存储 WebSocket 连接与 sessionId 的映射
        self.active_connections = {}
        # 音色
        self.voice = kwargs.get("voice", "x4_lingxiaoxuan_oral")
        # 语速
        self.rate = kwargs.get("rate", 50)
        # 音量
        self.volume = kwargs.get("volume", 50)
        self.audio_format = kwargs.get("audio_format", "mp3")
        self.api_key = xunfei_constants.API_KEY
        self.api_secret = xunfei_constants.SECRET_KEY
        self.api_url = xunfei_constants.TTS_API_URL
        self.appid = xunfei_constants.APP_ID
        self.audio_format_mapping = {
            'pcm': "raw",
            'mp3': "lame",
        }
        self.s3_client = CustomOSSClient()

    def on_message(self, ws, message):
        result_json = {
            "code": 0,
            "status": 0,
            "audio": "",
        }
        logging.info("接收来自讯飞的数据: %s", message)
        try:
            message = json.loads(message)
            code = message["header"]["code"]
            sid = message["header"]["sid"]
            result_json['code'] = code
            if code != 0:
                errMsg = message["header"]["message"]
                logging.error("sid:%s call error:%s code is:%s", sid, errMsg, code)
                if 'length must be larger or equal than 1' in errMsg:
                    # 当做成功
                    result_json['code'] = 0
                    result_json['status'] = 2
                    logging.info("result_json: %s", str(result_json))
                    # asyncio.run(send_message_to_session(ws.session_id, json.dumps(__response_data(ws, result_json))))
                    # 把数据添加到队列中，并且累计完整数据
                    self.__add_queue_response_data(ws, result_json)
                    ws.end_time = time.time()
                    print("ws is closed")
                    ws.close()
                else:
                    if code == 11201:
                        logging.error('讯飞用完了的免费额度，请充值或者更换账号')
                        self.__add_queue_response_data(ws, {
                            "code": 1100,
                            "errorMsg": "语音服务器异常"
                        })
                    else:
                        logging.error('讯飞服务器返回错误码：%s', str(code))
                        self.__add_queue_response_data(ws, {
                            "code": 1101,
                            "errorMsg": "服务器异常，稍后再试"
                        })
            if ("payload" in message):
                audio = message["payload"]["audio"]['audio']
                # audio = base64.b64decode(audio)
                status = message["payload"]['audio']["status"]
                result_json['status'] = status
                result_json["audio"] = audio
                logging.info("result_json: %s", str(result_json))
                # 把数据添加到队列中，并且累计完整数据
                self.__add_queue_response_data(ws, result_json)
                if status == 2:
                    print("ws is closed")
                    ws.end_time = time.time()
                    ws.close()
        except Exception as e:
            print("receive msg,but parse exception:", e)
            logging.exception(e)

    # 收到websocket错误的处理
    def on_error(self, ws, error):
        # return 0
        logging.error("### error:%s", error)

    # 收到websocket关闭的处理
    def on_close(self, ws, ts, end):
        print("### closed ###")
        # print("ws总耗时：开始输出到结束", ws.end_time - ws.start_time)
        logging.info("\nws流式输出最后时间 Current time: %s", time.strftime("%H:%M:%S", time.localtime()))
        return 0

    # 收到websocket连接建立的处理
    def on_open(self, ws):
        logging.debug("on_open")


    def start_websocket_client(self, session_id):
        """
        开启websocket连接，并接收数据
        :param session_id: 会话ID
        :return:
        """
        # 从控制台页面获取以下密钥信息，控制台地址：https://console.xfyun.cn/app/myapp
        websocket.enableTrace(False)
        ws_url = get_authorization_url(self.api_url, self.api_key, self.api_secret)
        ws = websocket.WebSocketApp(ws_url, on_message=self.on_message, on_error=self.on_error, on_close=self.on_close)
        ws.on_open = self.on_open
        ws.session_id = session_id

        self.send_seqs[session_id] = 0
        self.active_connections[session_id] = ws
        ws.run_forever(sslopt={"cert_reqs": ssl.CERT_NONE})

    def send_message(self, session_id, message, status, params: dict = None):
        """
        发送数据
        :param session_id: 会话ID
        :param message: 发送的数据
        :param status: 发送的状态，0开始，1中间，2结束
        :param params: 参数
        :return:
        """
        logging.info("发送给讯飞的数据：session_id=" + session_id + ";message=" + message + ";" + "status：" + str(status))
        ws = self.active_connections[session_id]
        param = self.__init_send_param(session_id, message, status, params)
        ws.send(param)
        ws.start_time = time.time()
        self.send_seqs[session_id] += 1

    def __init_send_param(self, session_id, text, status, params: dict = None) -> str:
        seq = self.send_seqs[session_id]
        commonArgs = {"app_id": self.appid, "status": status}
        data = {
            "text": {
                "encoding": "utf8",
                "compress": "raw",
                "format": "plain",
                "status": status,
                "seq": seq,
                "text": str(base64.b64encode(text.encode('utf-8')), "UTF8")  # 待合成文本base64格式
            }
        }
        if params is None:
            params = {}
        d = {"header": commonArgs,
             "parameter": {
                 "tts": {
                     # 音色
                     "vcn": params.get("voice", self.voice),  # 发音人参数，更换不同的发音人会有不同的音色效果
                     "volume": params.get("volume", self.volume),  # 设置音量大小
                     "rhy": 0,  # 是否返回拼音标注		0:不返回拼音, 1:返回拼音（纯文本格式，utf8编码）
                     "speed": params.get("rate", self.rate),  # 设置合成语速，值越大，语速越快
                     "pitch": 50,  # 设置振幅高低，可通过该参数调整效果
                     "bgs": 0,  # 背景音	0:无背景音, 1:内置背景音1, 2:内置背景音2
                     "reg": 0,  # 英文发音方式 	0:自动判断处理，如果不确定将按照英文词语拼写处理（缺省）,
                     # 1:所有英文按字母发音, 2:自动判断处理，如果不确定将按照字母朗读
                     "rdn": 0,  # 合成音频数字发音方式	0:自动判断, 1:完全数值, 2:完全字符串, 3:字符串优先
                     "audio": {
                         # 合成音频格式， lame 合成音频格式为mp3
                         "encoding": self.audio_format_mapping[params.get("audio_format", self.audio_format)],
                         "sample_rate": 16000,  # 合成音频采样率，	16000, 8000, 24000
                         "channels": 1,  # 音频声道数
                         "bit_depth": 16,  # 合成音频位深 ：16, 8
                         "frame_size": 0
                     }
                 },
                 # 口语化设置
                 "oral": {
                     # 口语化等级	string	高:high, 中:mid, 低:low	否	mid
                     "oral_level": "mid",
                     # 是否通过大模型进行口语化	int	开启:1, 关闭:0
                     "spark_assist": 1,
                     # 关闭服务端拆句	int	不关闭：0，关闭：1
                     "stop_split": 1,
                     # 是否保留原书面语的样子	int	保留:1, 不保留:0
                     "remain": 1
                 }
             },
             "payload": data,
             }
        d = json.dumps(d)
        return d

    def __add_queue_response_data(self, ws, result_json):
        logging.info("__add_queue_response_data: %s", str(result_json))
        audio = result_json["audio"]
        status = result_json['status']
        if status == 2:
            # 需要判断一下状态为2的时候，是否还有一段语音数据
            if audio is not None and audio != '':
                logging.info("__add_queue_response_data: 最后一段有数据")
                self.queue_manager.put_end(ws.session_id, audio)
            else:
                self.queue_manager.put_end(ws.session_id, "")
        else:
            self.queue_manager.put(ws.session_id, audio)


def get_authorization_url(api_url, api_key, api_secret):
    """
    获取已经鉴权的url
    :param api_url: 基础URL
    :param api_key: key
    :param api_secret: 秘钥
    :return:
    """
    u = parse_url(api_url)
    host = u.host
    path = u.path
    now = datetime.now()
    date = format_date_time(time.mktime(now.timetuple()))
    print(date)
    # date = "Thu, 12 Dec 2019 01:57:27 GMT"
    signature_origin = f"host: {host}\ndate: {date}\nGET {path} HTTP/1.1"
    # print(signature_origin)
    signature_sha = hmac.new(api_secret.encode('utf-8'), signature_origin.encode('utf-8'),
                             digestmod=hashlib.sha256).digest()
    signature_sha = base64.b64encode(signature_sha).decode(encoding='utf-8')
    authorization_origin = (f"api_key=\"{api_key}\", algorithm=\"hmac-sha256\", "
                            f"headers=\"host date request-line\", signature=\"{signature_sha}\"")
    authorization = base64.b64encode(authorization_origin.encode('utf-8')).decode(encoding='utf-8')
    # print(authorization_origin)
    values = {
        "host": host,
        "date": date,
        "authorization": authorization
    }
    return api_url + "?" + urlencode(values)

def parse_url(request_url):
    """
    解析url
    :param request_url:
    :return:
    """
    stidx = request_url.index("://")
    host = request_url[stidx + 3:]
    schema = request_url[:stidx + 3]
    edidx = host.index("/")
    if edidx <= 0:
        raise AssembleHeaderException("invalid request url:" + request_url)
    path = host[edidx:]
    host = host[:edidx]
    u = Url(host, path, schema)
    return u

class AssembleHeaderException(Exception):
    def __init__(self, msg):
        self.message = msg


class Url:
    def __init__(this, host, path, schema):
        this.host = host
        this.path = path
        this.schema = schema
        pass


if __name__ == '__main__':
    import asyncio
    url, duration = asyncio.run(XunfeiTTSBase().tts_by_xunfei("hello"))
    print(url)
    print(duration)

    queue_manager = QueueManager()
    xunfei = XunfeiTTSStream(queue_manager)

    import threading
    thread = threading.Thread(target=xunfei.start_websocket_client, args=("123",))
    thread.daemon = True  # 主线程结束时自动结束
    thread.start()

    sleep(3)
    xunfei.send_message("123", "hello", 2)
    while "123" not in queue_manager.queues:
        sleep(3)

    while not queue_manager.queues["123"].empty():
        print(queue_manager.get("123"))
        # break
