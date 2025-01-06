import asyncio
import base64
import logging
from queue import Queue

from edge_tts import Communicate

from suncodes_ai_chat.suncodes_common.base_stream.queue_manager import QueueManager
from suncodes_ai_chat.suncodes_utils.md_text import markdown_to_text

logging = logging.getLogger(__name__)


async def async_tts_bytes(text, voice, rate, volume) -> bytearray:
    """
    TTS
    :param text:
    :param voice:
    :param rate:
    :param volume:
    :return:
    """
    audio_bytes = bytearray()
    communicate = Communicate(text=text, voice=voice, rate=rate, volume=volume)
    logging.info("Starting TTS streaming...")
    num = 0
    # 逐片段获取语音数据
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":  # 仅处理音频数据
            audio = chunk["data"]
            audio_bytes.extend(audio)
            num += 1
            # print(f"Audio chunk received: {len(chunk['data'])} bytes")

    logging.info("Audio data received: %s bytes, num chunk: %s", len(audio_bytes), num)
    logging.info("Streaming completed.")
    return audio_bytes


async def retry_async(func, *args, **kwargs):
    """
    异步重试
    :param func:
    :param args:
    :param kwargs:
    :return:
    """
    retry_total_num = 3
    for retry_i in range(retry_total_num):
        try:
            logging.info("重试 %s 次", retry_i)
            return await func(*args, **kwargs)
        except Exception as e:
            logging.exception(e)
            if retry_i == retry_total_num - 1:
                logging.info("重试 %s 次失败，返回空", retry_total_num)
                # 如果重试后依旧失败，则原异常抛出
                raise e
            await asyncio.sleep(1)


class EdgeTTSBase:
    """
    只支持输出mp3
    """

    def __init__(self, **kwargs):
        # 音色
        self.voice = kwargs.get("voice", "en-US-JennyNeural")
        # 语速
        self.rate = kwargs.get("rate", "-20%")
        # 音量
        self.volume = kwargs.get("volume", "+0%")

    async def tts_by_edge(self, text: str, params: dict = None) -> str:
        """
        TTS
        :param text:
        :param params:
        :return:
        """
        text_escape = markdown_to_text(text)
        logging.info("tts_by_edge 原始文本：%s, md格式去除后文本：%s", text, text_escape)
        if text_escape is None or text_escape == "":
            return ""
        if params is None:
            params = {}
        voice = params.get("voice")
        rate = params.get("rate")
        volume = params.get("volume")
        if voice is None:
            voice = self.voice
        if rate is None:
            rate = self.rate
        if volume is None:
            volume = self.volume

        audio_bytes = await retry_async(async_tts_bytes, text_escape, voice, rate, volume)
        return str(base64.b64encode(audio_bytes), 'utf-8')


class EdgeTTSStream:
    """
    流式tts
    """

    def __init__(self, queue_manager: QueueManager, **kwargs):
        # 音色
        self.voice = kwargs.get("voice", "en-US-JennyNeural")
        # 语速
        self.rate = kwargs.get("rate", "-20%")
        # 音量
        self.volume = kwargs.get("volume", "+0%")
        self.queue_manager = queue_manager
        self.queue = {}

    def stream_tts(self, session_id: str, text: str, status: int, params: dict = None):
        """
        流式tts 入口
        :param session_id:
        :param text:
        :param status:
        :param params:
        :return:
        """
        logging.info("EdgeTTS--Session %s: Streaming TTS for %s.", session_id, text)
        if params is None:
            params = {}
        voice = params.get("voice")
        rate = params.get("rate")
        volume = params.get("volume")
        if not session_id in self.queue:
            self.queue[session_id] = Queue()
            self.queue[session_id].put({
                "text": text,
                "status": status,
                "voice": voice or self.voice,
                "rate": rate or self.rate,
                "volume": volume or self.volume
            })
            if not self.__is_event_loop_running():
                asyncio.run(self.__stream_tts_queue(session_id))
            else:
                asyncio.create_task(self.__stream_tts_queue(session_id))
        else:
            self.queue[session_id].put({
                "text": text,
                "status": status,
                "voice": voice or self.voice,
                "rate": rate or self.rate,
                "volume": volume or self.volume
            })

    async def __stream_tts_queue(self, session_id: str):
        while True:
            try:
                data = self.queue[session_id].get()
                status = data["status"]
                await self.__stream_tts(session_id, data["text"], status, data["voice"], data["rate"], data["volume"])
                if status == 2:
                    if session_id in self.queue:
                        del self.queue[session_id]
                    break
            except asyncio.TimeoutError:
                logging.error("Timeout while waiting for data.")
                if session_id in self.queue:
                    del self.queue[session_id]
                pass
        pass

    async def __stream_tts(self, session_id: str, text: str, status: int,
                           voice: str = None, rate: str = None, volume: str = None):
        """
        使用 edge-tts 实现语音合成并流式输出到文件
        :param text: 要合成的文本
        :param voice: 使用的语音名称
        :param rate: 语速调整，例如 "+10%" 或 "-10%"
        :param volume: 音量
        """
        if voice is None:
            voice = self.voice
        if rate is None:
            rate = self.rate
        if volume is None:
            volume = self.volume

        text_escape = markdown_to_text(text)
        logging.info("tts_by_edge 原始文本：%s, md格式去除后文本：%s", text, text_escape)
        logging.info(" %s Starting TTS streaming...", session_id)
        if text_escape is not None and text_escape.strip() != "":
            audio_bytes = await retry_async(async_tts_bytes, text_escape, voice, rate, volume)
            self.queue_manager.put(session_id, str(base64.b64encode(audio_bytes), 'utf-8'))
        else:
            logging.warning("%s edge-tts __stream_tts 没有文本需要转语音，忽略！", session_id)

        if status == 2:
            self.queue_manager.put_end(session_id, "")
        logging.info("%s Streaming completed.", session_id)

    # 判断当前事件循环是否运行
    @staticmethod
    def __is_event_loop_running():
        """
        判断当前事件循环是否在运行
        :return:
        """
        try:
            # 获取当前事件循环
            loop = asyncio.get_event_loop()
            # 检查事件循环是否已经运行
            return loop.is_running()
        except RuntimeError:
            # 如果没有事件循环，则说明没有运行中的事件循环
            return False


# 主函数执行
if __name__ == "__main__":
    text_to_synthesize = "Hello, this is a streaming text-to-speech example using edge-tts."
    tts_queue_manager = QueueManager()
    edge_tts = EdgeTTSStream(tts_queue_manager)
    session_id = '1234'
    edge_tts.stream_tts(session_id, text_to_synthesize, 2)

    while not tts_queue_manager.queues[session_id].empty():
        print(tts_queue_manager.get(session_id))
