import logging

from suncodes_ai_chat.suncodes_common.asr.baidu_asr import BaiduASRBase
from suncodes_ai_chat.suncodes_common.asr.xunfei_asr import XunfeiASRBase
from suncodes_ai_chat.suncodes_common.base_chain.custom_chain import CustomLLMChain
from suncodes_ai_chat.suncodes_common.oss.oss_cli import CustomOSSClient
from suncodes_ai_chat.suncodes_common.tts.baidu_tts import BaiduTTSBase
from suncodes_ai_chat.suncodes_common.tts.xunfei_tts import XunfeiTTSBase
from suncodes_ai_chat.suncodes_common.tts.custom_edge_tts import EdgeTTSBase
from suncodes_ai_chat.suncodes_document import doc_settings
from suncodes_ai_chat.suncodes_utils.file_base64 import read_file_content
from suncodes_ai_chat.suncodes_model.base_chat.base_chat import (BaseAskQuery, BaseTextAskQuery, BaseAskVO, WsAskVO)
from suncodes_ai_chat.suncodes_app.base_chat.base_chat_stream_handler import (
    EdgeTTSHandler, InputHandler, LLMModelHandler, OutputHandler, TTSHandler)
from suncodes_ai_chat.suncodes_common.base_stream.pipeline_stream import PipelineStream
from suncodes_ai_chat.suncodes_common.base_stream.queue_manager import QueueManager
from suncodes_ai_chat.suncodes_common.cache.memory_cache import memory_cache
from suncodes_ai_chat.suncodes_common.websocket_pool.websocket_manager import \
    send_message_to_session
from suncodes_ai_chat.suncodes_model.enums.error_enum import ErrorStatusEnum
from suncodes_ai_chat.suncodes_model.enums.role_ai_code_enum import RoleAICodeEnum

oss_client = CustomOSSClient()
xxt_edge_tts = EdgeTTSBase()
xunfei_tts = XunfeiTTSBase()
baidu_tts = BaiduTTSBase()
llm_chain = CustomLLMChain()

logging = logging.getLogger(__name__)


async def ai_chat_stream(session_id, send_data):
    """
        语音 --> 文字 --> AI ---> 文字 --> 语音
        :param item:
        :return:
        """

    ask_item = BaseAskQuery.model_validate_json(send_data)
    logging.info("入参：sessionId=%s，参数：%s", session_id, ask_item)
    # 校验参数

    url = ask_item.userAudioUrl
    role_code = ask_item.roleCode
    if role_code is None or url is None or url == '':
        error_code = ErrorStatusEnum.INPUT_TEXT.error_code
        ask_response_item = WsAskVO(type=1, status=500, code=error_code, message="参数错误")
        response = ask_response_item.model_dump_json()
        logging.error("AI回答：%s", response)
        await send_message_to_session(session_id, response)
        return

    ask_item.sessionId = session_id
    user_url = ask_item.userAudioUrl

    try:
        speech_text_json = await speech_to_text(user_url, asr_model="xunfei", language="zh")
        myself_text = speech_text_json['myselfText']
    except Exception as e:
        logging.exception(e)
        myself_text = '语音转文字失败'

    logging.info("daily_ai_chat_stream 语音转文字结果：%s", myself_text)

    if myself_text is None or myself_text.strip() == '':
        error_code = ErrorStatusEnum.NO_SPEAK.error_code
        ask_response_item = WsAskVO(type=1, status=500, code=error_code, message="未识别到您说话，请重新说话")
        response = ask_response_item.model_dump_json()
        logging.error("AI回答：%s", response)

        await send_message_to_session(session_id, response)
        return

    if myself_text == '语音转文字失败':
        error_code = ErrorStatusEnum.SPEECH_FAIL.error_code
        ask_response_item = WsAskVO(type=1, status=500, code=error_code, message=myself_text)
        response = ask_response_item.model_dump_json()
        logging.error("AI回答：%s", response)

        await send_message_to_session(session_id, response)
        return

    await __ask_stream(ask_item, myself_text)


async def ai_chat_text_stream(session_id, send_data):
    """
    文字 --> AI ---> 文字 --> 语音
    """
    ask_item = BaseTextAskQuery.model_validate_json(send_data)
    logging.info("入参：sessionId=%s，参数：%s", session_id, ask_item)
    ask_item.sessionId = session_id
    await __ask_stream(ask_item, ask_item.text)


async def __ask_stream(ask_item, text):
    """
        语音 --> 文字 --> AI ---> 文字 --> 语音
        :param ask_item: 会话ID
        :param text: 用户说的话
        :return:
        """
    websocket_queue_manager = QueueManager()
    input_queue_manager = QueueManager()
    llm_queue_manager = QueueManager()
    tts_queue_manager = QueueManager()
    intput_handler = InputHandler(websocket_queue_manager, input_queue_manager)
    llm_handler = LLMModelHandler(input_queue_manager, llm_queue_manager)
    # tts_handler = TTSHandler(llm_queue_manager, tts_queue_manager)
    tts_handler = EdgeTTSHandler(llm_queue_manager, tts_queue_manager)
    output_handler = OutputHandler(tts_queue_manager)

    session_id = ask_item.sessionId
    pipline = PipelineStream(handlers=[intput_handler, llm_handler, tts_handler, output_handler], cache=True)
    pipline.cache_manager.set_data(session_id, ask_item.model_dump_json())
    pipline.start(session_id).pipeline(session_id, text)


async def base_ask(query: BaseAskQuery):
    """
    语音 --> 文字 --> AI ---> 文字 --> 语音
    :param item:
    :return:
    """
    logging.info("base_ask 入参", query)
    speech_text_json = await speech_to_text(query.userAudioUrl, "xunfei", "zh")
    myself_text = speech_text_json['myselfText']
    if myself_text == '语音转文字失败':
        return BaseAskVO(myselfText=myself_text)
    # 调用大模型
    ai_answer = get_ai_response(myself_text, "deepseek", '', query.sessionId)
    # 语音合成
    speech = await text_to_speech(ai_answer['speechText'], 'edge-tts')
    return BaseAskVO(myselfText=myself_text, speechText=ai_answer['speechText'], speech=speech['speech'],
                     time=speech['time']).model_dump_json()


async def base_text_ask(query: BaseTextAskQuery):
    logging.info("base_text_ask 入参", query)
    role_code = query.roleCode
    prompt_url = RoleAICodeEnum.get_enum_by_role_code(role_code).prompt_url
    prompt = read_file_content(prompt_url)
    # 调用大模型
    ai_answer = get_ai_response(query.text, "deepseek", prompt, query.sessionId)
    # 语音合成
    speech = await text_to_speech(ai_answer['speechText'], 'edge-tts')
    return BaseAskVO(myselfText=query.text, speechText=ai_answer['speechText'], speech=speech['speech'],
                     time=speech['time'])


async def speech_to_text(audio_url: str, asr_model: str = "xunfei", language: str = 'en') -> dict:
    """
    语音转文字
    :param audio_url:
    :param asr_model:
    :param language:
    :return:
    """
    logging.info("speech_to_text input url：%s", audio_url)
    logging.info("speech_to_text input model：%s", asr_model)

    base64_encoded = oss_client.download_base64_file(audio_url)

    speech_text = ''
    if asr_model == 'baidu':
        res = BaiduASRBase().asr_by_baidu(base64_encoded)
        result = ["语音转文字失败"]
        if res["err_msg"] == 'success.':
            result = res["result"]
        speech_text = ','.join(result)
    if asr_model == 'xunfei':
        speech_text = await XunfeiASRBase(language=language).asr_by_xunfei(base64_encoded)
    return {"myselfText": speech_text}


async def text_to_speech(text, tts_model):
    """
    TTS合成
    :param text:
    :param tts_model:
    :return:
    """
    logging.info("text_to_speech input text, tts_model：" + text + "," + tts_model)
    response_speech = ''
    time = 0
    if tts_model == 'xunfei':
        response_speech, time = await xunfei_tts.tts_by_xunfei(text)
    if tts_model == 'baidu':
        response_speech, time = baidu_tts.tts_by_baidu(text)
    if tts_model == 'edge-tts':
        response_speech, time = await xxt_edge_tts.tts_by_edge(text)
    return {"speech": response_speech, "time": time}


def get_ai_response(question, llm_model, prompt, session_id):
    """
    获取AI回答
    """
    logging.info("model input：%s", question)
    # 调用大模型
    if prompt is None or prompt == '':
        prompt = read_file_content(doc_settings.PROMPT_BAIKE)
    ai_answer = llm_chain.run(question, session_id, prompt, llm_model)
    logging.info("model output：%s", ai_answer)
    return {"speechText": ai_answer}
