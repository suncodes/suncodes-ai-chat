import asyncio
import base64
import datetime
import json
import logging
import math
import threading

from suncodes_ai_chat.suncodes_common.base_chain.custom_chain import CustomLLMChainStream
from suncodes_ai_chat.suncodes_common.base_stream.queue_manager import QueueManager
from suncodes_ai_chat.suncodes_common.base_stream.stream_cache_manager import \
    StreamCacheManager
from suncodes_ai_chat.suncodes_common.base_stream.stream_handler import (
    StreamHandler, before_call_check_error, is_event_loop_running)
from suncodes_ai_chat.suncodes_common.oss.oss_cli import CustomOSSClient
from suncodes_ai_chat.suncodes_common.tts.xunfei_tts import XunfeiTTSStream
from suncodes_ai_chat.suncodes_common.tts.custom_edge_tts import EdgeTTSStream
from suncodes_ai_chat.suncodes_common.websocket_pool.websocket_manager import (
    send_message_to_session, send_message_to_session_and_close)
from suncodes_ai_chat.suncodes_model.base_chat.base_chat import (StreamCacheModel, WsAskVO)
from suncodes_ai_chat.suncodes_model.enums.error_enum import ErrorStatusEnum
from suncodes_ai_chat.suncodes_model.enums.role_ai_code_enum import RoleAICodeEnum
from suncodes_ai_chat.suncodes_utils.file_base64 import (get_mp3_duration,
                                                         read_file_content)
from suncodes_ai_chat.suncodes_common.cache.memory_cache import memory_cache
from suncodes_ai_chat.suncodes_common.cache import cache_key
from suncodes_ai_chat.suncodes_utils.random_string import generate_random_string

logging = logging.getLogger(__name__)


def before_call_intercept_error(cache_manager: StreamCacheManager, session_id: str):
    common_data = cache_manager.get_data(session_id)
    cache = StreamCacheModel.model_validate_json(common_data)
    if cache.status is None:
        logging.warning("%s此时缓存已经被清除掉了，不再往下走了", session_id)
        return
    cache_manager.remove_data(session_id)
    ask_response = WsAskVO(type=2, status=500, message=cache.message, code=cache.code)
    if not is_event_loop_running():
        asyncio.run(send_message_to_session_and_close(session_id, ask_response.model_dump_json()))
    else:
        asyncio.create_task(send_message_to_session_and_close(session_id, ask_response.model_dump_json()))
        pass
    pass


class InputHandler(StreamHandler):
    def __init__(self, input_queue_manager: QueueManager, output_queue_manager: QueueManager):
        super().__init__(input_queue_manager, output_queue_manager)

    @before_call_check_error
    def on_stream_chunk(self, data: str, session_id: str, status: int):
        """
        处理数据
        """
        if status == 2:
            self.output_queue_manager.put_end(session_id, data)
        else:
            self.output_queue_manager.put(session_id, data)
        pass

    @before_call_check_error
    def on_stream_end(self, session_id: str):
        """
        结束
        """
        # 获取所有数据（相当于清空队列）
        all_data = ""
        while not self.input_queue_manager.queues[session_id].empty():
            all_data = all_data + self.input_queue_manager.get(session_id)

        common_data = self.cache_manager.get_data(session_id)
        cache = StreamCacheModel.model_validate_json(common_data)
        if cache.roleCode is None:
            logging.error("%s InputHandler on_stream_end 此时缓存已经被清除掉了，不再往下走了", session_id)
            return

        cache.question = all_data
        cache.chatId = generate_random_string(12)
        self.cache_manager.set_data(session_id, cache.model_dump_json())

        if all_data is None or all_data.strip() == "":
            cache.status = 500
            cache.code = ErrorStatusEnum.INPUT_TEXT.error_code
            cache.message = "没有检测到您说话"
            self.cache_manager.set_data(session_id, cache.model_dump_json())

    @before_call_check_error
    def on_self_stream_chunk(self, data: str, session_id: str, status: int):
        """
        自己输出流的回调函数
        """
        ask_response = WsAskVO(type=1, streamStatus=1, myselfText=data)
        if not is_event_loop_running():
            asyncio.run(send_message_to_session(session_id, ask_response.model_dump_json()))
        else:
            asyncio.create_task(send_message_to_session(session_id, ask_response.model_dump_json()))
        pass

    def on_before_check_error(self, session_id: str):
        """
        开始之前检查流是否错误
        """
        before_call_intercept_error(self.cache_manager, session_id)
        pass


class LLMModelHandler(StreamHandler):
    def __init__(self, input_queue_manager: QueueManager, output_queue_manager: QueueManager):
        super().__init__(input_queue_manager, output_queue_manager)
        self.llm = CustomLLMChainStream(self.output_queue_manager, temperature=1)
        # self.datas = {}
        self.seqs = {}

    @before_call_check_error
    def on_stream_end(self, session_id: str):
        """
        处理数据
        """
        all_data = ""
        while not self.input_queue_manager.queues[session_id].empty():
            all_data = all_data + self.input_queue_manager.get(session_id)
        if all_data is None or all_data.strip() == "":
            common_data = self.cache_manager.get_data(session_id)
            cache = StreamCacheModel.model_validate_json(common_data)
            cache.status = 500
            cache.code = ErrorStatusEnum.INPUT_TEXT.error_code
            cache.message = "没有检测到您说话"
            self.cache_manager.set_data(session_id, cache.model_dump_json())
            return
        # 请求接口，获取Prompt
        common_data = self.cache_manager.get_data(session_id)
        cache = StreamCacheModel.model_validate_json(common_data)
        if cache.roleCode is None:
            logging.error("%s LLMModelHandler on_stream_end 此时缓存已经被清除掉了，不再往下走了", session_id)
            return
        if memory_cache.exists_key(cache_key.DAILY_PROMPT_CACHE_KEY.format(cache.roleCode)):
            prompt = memory_cache.get_cache(cache_key.DAILY_PROMPT_CACHE_KEY.format(cache.roleCode))
        else:
            prompt_url = RoleAICodeEnum.get_enum_by_role_code(cache.roleCode).prompt_url
            if prompt_url is None or prompt_url == "":
                logging.error("%s获取提示词为空", session_id)
                common_data = self.cache_manager.get_data(session_id)
                cache = StreamCacheModel.model_validate_json(common_data)
                cache.status = 500
                cache.code = ErrorStatusEnum.PROMPT_FAIL.error_code
                cache.message = "服务器错误，请稍后重试"
                self.cache_manager.set_data(session_id, cache.model_dump_json())
                return
            prompt = read_file_content(prompt_url)
            # 缓存
            memory_cache.add_cache(cache_key.DAILY_PROMPT_CACHE_KEY.format(cache.roleCode), prompt)
        # 还需要创建线程，异步评价问题等级
        self.llm.run(all_data, session_id=session_id, prompt=prompt)
        pass

    @before_call_check_error
    def on_self_stream_chunk(self, data: str, session_id: str, status: int):
        """
        自己输出流的回调函数
        """
        self.seqs[session_id] = self.seqs.get(session_id, 0) + 1
        # 发送数据到 websocket
        ask_response = WsAskVO(type=2, streamStatus=1, speechText=data, textSeq=self.seqs[session_id])
        if not is_event_loop_running():
            asyncio.run(send_message_to_session(session_id, ask_response.model_dump_json()))
        else:
            asyncio.create_task(send_message_to_session(session_id, ask_response.model_dump_json()))
        pass

    def on_before_check_error(self, session_id: str):
        """
        开始之前检查流是否错误
        """
        before_call_intercept_error(self.cache_manager, session_id)
        pass


class TTSHandler(StreamHandler):
    def __init__(self, input_queue_manager: QueueManager, output_queue_manager: QueueManager):
        super().__init__(input_queue_manager, output_queue_manager)
        self.tts = XunfeiTTSStream(self.output_queue_manager)
        self.seqs = {}
        self.tmp_data = {}
        self.merge_chunk = 20

    @before_call_check_error
    def on_stream_start(self, session_id: str):
        thread = threading.Thread(target=self.tts.start_websocket_client, args=(session_id,))
        thread.daemon = True  # 主线程结束时自动结束
        thread.start()

    @before_call_check_error
    def on_stream_chunk(self, data: str, session_id: str, status: int):
        """
        处理数据
        """
        # 请求的数据
        self.tts.send_message(session_id, data, status)
        pass

    @before_call_check_error
    def on_stream_end(self, session_id: str):
        """
        处理数据
        """
        all_data = ""
        while not self.input_queue_manager.queues[session_id].empty():
            all_data = all_data + self.input_queue_manager.get(session_id)
        # 暂时不请求接口，先缓存数据，最后一起更新数据
        common_data = self.cache_manager.get_data(session_id)
        cache = StreamCacheModel.model_validate_json(common_data)
        cache.answer = all_data
        self.cache_manager.set_data(session_id, cache.model_dump_json())
        pass

    @before_call_check_error
    def on_stream_error(self, session_id: str, error_code: int, reason: str):
        """
        流出现了异常
        """
        logging.error("on_stream_error 流发生了错误：session_id: %s, error_code: %d, reason: %s",
                      session_id, error_code, reason)
        common_data = self.cache_manager.get_data(session_id)
        cache = StreamCacheModel.model_validate_json(common_data)
        cache.status = 500
        cache.code = ErrorStatusEnum.LLM_RESPONSE_FAIL.error_code
        cache.message = reason
        self.cache_manager.set_data(session_id, cache.model_dump_json())
        self.cache_manager.set_data(session_id, cache.model_dump_json())

    @before_call_check_error
    def on_self_stream_chunk(self, data: str, session_id: str, status: int):
        """
        自己输出流的回调函数
        """
        self.seqs[session_id] = self.seqs.get(session_id, 0) + 1
        self.__add_tmp_data(data, session_id)
        if status == 2:
            self.__send_merged_audio(session_id)
            del self.tmp_data[session_id]
            pass
        else:
            if self.seqs[session_id] % self.merge_chunk == 0:
                self.__send_merged_audio(session_id)
                del self.tmp_data[session_id]
                pass
        pass

    def on_before_check_error(self, session_id: str):
        """
        开始之前检查流是否错误
        """
        before_call_intercept_error(self.cache_manager, session_id)
        pass

    def __add_tmp_data(self, data: str, session_id: str):
        if session_id not in self.tmp_data:
            self.tmp_data[session_id] = bytearray()
        audio = self.tmp_data[session_id]
        audio_bytes = base64.b64decode(data)
        audio.extend(audio_bytes)

    def __send_merged_audio(self, session_id: str):
        audio = self.tmp_data[session_id]
        audio_str = str(base64.b64encode(audio), 'utf-8')
        if audio_str is None or audio_str == '':
            return None
        # 发送数据到 websocket
        ask_response = WsAskVO(type=3, streamStatus=1, audio=audio_str,
                               audioSeq=int(math.ceil(self.seqs[session_id] / self.merge_chunk)))
        if not is_event_loop_running():
            asyncio.run(send_message_to_session(session_id, ask_response.model_dump_json()))
        else:
            asyncio.create_task(send_message_to_session(session_id, ask_response.model_dump_json()))
        pass


class EdgeTTSHandler(StreamHandler):
    def __init__(self, input_queue_manager: QueueManager, output_queue_manager: QueueManager):
        super().__init__(input_queue_manager, output_queue_manager)
        self.tts = EdgeTTSStream(self.output_queue_manager)
        self.seqs = {}
        self.tmp_data = {}
        self.merge_chunk = 1

    @before_call_check_error
    def on_stream_chunk(self, data: str, session_id: str, status: int):
        """
        处理数据
        """
        voice = "zh-CN-XiaoyiNeural"
        # 请求的数据
        self.tts.stream_tts(session_id, data, status, params={
            # edge-tts -l
            # "voice": "zh-CN-YunxiaNeural",
            "voice": voice,
            "rate": "-10%",
        })
        pass

    @before_call_check_error
    def on_stream_end(self, session_id: str):
        """
        处理数据
        """
        all_data = ""
        while not self.input_queue_manager.queues[session_id].empty():
            all_data = all_data + self.input_queue_manager.get(session_id)
        # 请求接口，写答案
        common_data = self.cache_manager.get_data(session_id)
        cache = StreamCacheModel.model_validate_json(common_data)
        cache.answer = all_data
        self.cache_manager.set_data(session_id, cache.model_dump_json())
        pass

    @before_call_check_error
    def on_stream_error(self, session_id: str, error_code: int, reason: str):
        """
        流出现了异常
        """
        logging.error("on_stream_error 流发生了错误：session_id: %s, error_code: %d, reason: %s",
                      session_id, error_code, reason)
        common_data = self.cache_manager.get_data(session_id)
        cache = StreamCacheModel.model_validate_json(common_data)
        cache.status = 500
        cache.code = ErrorStatusEnum.LLM_RESPONSE_FAIL.error_code
        cache.message = reason
        self.cache_manager.set_data(session_id, cache.model_dump_json())

    @before_call_check_error
    def on_self_stream_chunk(self, data: str, session_id: str, status: int):
        """
        自己输出流的回调函数
        """
        self.seqs[session_id] = self.seqs.get(session_id, 0) + 1
        self.__add_tmp_data(data, session_id)
        if status == 2:
            self.__send_merged_audio(session_id)
            del self.tmp_data[session_id]
            pass
        else:
            if self.seqs[session_id] % self.merge_chunk == 0:
                self.__send_merged_audio(session_id)
                del self.tmp_data[session_id]
                pass
        pass

    def on_before_check_error(self, session_id: str):
        """
        开始之前检查流是否错误
        """
        before_call_intercept_error(self.cache_manager, session_id)
        pass

    def __add_tmp_data(self, data: str, session_id: str):
        if session_id not in self.tmp_data:
            self.tmp_data[session_id] = bytearray()
        audio = self.tmp_data[session_id]
        audio_bytes = base64.b64decode(data)
        audio.extend(audio_bytes)

    def __send_merged_audio(self, session_id: str):
        audio = self.tmp_data[session_id]
        audio_str = str(base64.b64encode(audio), 'utf-8')
        if audio_str is None or audio_str == '':
            return None
        # 发送数据到 websocket
        ask_response = WsAskVO(type=3, streamStatus=1, audio=audio_str,
                               audioSeq=int(math.ceil(self.seqs[session_id] / self.merge_chunk)))
        if not is_event_loop_running():
            asyncio.run(send_message_to_session(session_id, ask_response.model_dump_json()))
        else:
            asyncio.create_task(send_message_to_session(session_id, ask_response.model_dump_json()))
        pass


class OutputHandler(StreamHandler):
    def __init__(self, input_queue_manager: QueueManager):
        super().__init__(input_queue_manager, None)
        self.datas = {}
        self.oss_client = CustomOSSClient()

    @before_call_check_error
    def on_stream_end(self, session_id: str):
        """
        处理数据
        """
        common_data = self.cache_manager.get_data(session_id)
        cache = StreamCacheModel.model_validate_json(common_data)
        if cache.roleCode is None:
            logging.error("%s OutputHandler on_stream_end 缓存数据为空", session_id)
            return
        all_data_bytes = bytearray()
        while not self.input_queue_manager.queues[session_id].empty():
            # all_data = all_data + self.input_queue_manager.get(session_id)
            audio = self.input_queue_manager.get(session_id)
            if audio is None or audio == '':
                continue
            import base64
            audio_bytes = base64.b64decode(audio)
            all_data_bytes.extend(audio_bytes)

        # 上传s3
        speech_url = self.oss_client.upload_file_random_path(all_data_bytes)
        duration = get_mp3_duration(all_data_bytes)

        cache.answerAudioUrl = speech_url
        # 请求接口，更新回答
        logging.info("%s 检查数据：%s", session_id, cache)
        if cache.chatId is None:
            logging.error("%s OutputHandler 在前一步创建聊天记录失败，后续无法更新聊天记录数据", session_id)
            error_code = ErrorStatusEnum.UPDATE_CHAT_FAIL.error_code
            reason = "服务器错误，请稍后重试"
            ask_response = WsAskVO(type=3, status=500, code=error_code, message=reason)
            if not is_event_loop_running():
                asyncio.run(send_message_to_session(session_id, ask_response.model_dump_json()))
            else:
                asyncio.create_task(send_message_to_session(session_id, ask_response.model_dump_json()))
            return

        # 不管成功不成功，只要回答结束，就清空缓存
        self.cache_manager.remove_data(session_id)
        ask_response = WsAskVO(type=3, streamStatus=2, speech=speech_url, time=duration, chatId=cache.chatId)
        if not is_event_loop_running():
            asyncio.run(send_message_to_session(session_id, ask_response.model_dump_json()))
        else:
            asyncio.create_task(send_message_to_session(session_id, ask_response.model_dump_json()))
        pass

    def on_before_check_error(self, session_id: str):
        """
        开始之前检查流是否错误
        """
        before_call_intercept_error(self.cache_manager, session_id)
        pass
