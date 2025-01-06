import logging
import random
import re
import string
import time
from time import sleep
from urllib.parse import quote_plus as urlquote

from openai import OpenAIError, RateLimitError, AuthenticationError
from langchain.callbacks.base import BaseCallbackHandler
from langchain.chains import LLMChain
from langchain.memory import ConversationBufferMemory
from langchain.prompts import (ChatPromptTemplate, HumanMessagePromptTemplate,
                               MessagesPlaceholder,
                               SystemMessagePromptTemplate)
from langchain_mongodb import MongoDBChatMessageHistory

from suncodes_ai_chat.suncodes_common.base_stream.queue_manager import QueueManager
from suncodes_ai_chat.suncodes_common.llm.doubao_llm import DouBaoAILLM
from suncodes_ai_chat.suncodes_common.llm.zhipu_llm import ZhipuAILLM
from suncodes_ai_chat.suncodes_common.llm.deepseek_llm import DeepseekAILLM
from suncodes_ai_chat.suncodes_config.config_manager import config_manager

logging = logging.getLogger(__name__)


def get_support_llm(llm_name: str, **kwargs):
    """
    初始化
    :param llm_name: 大厂名字
    :param kwargs: 参数
    """
    logging.info("目前使用的llm模型：%s", llm_name)
    if llm_name == "doubao":
        llm = DouBaoAILLM(**kwargs)
    elif llm_name == "zhipu":
        llm = ZhipuAILLM(**kwargs)
    elif llm_name == "deepseek":
        llm = DeepseekAILLM(**kwargs)
    else:
        raise ValueError("不支持的 LLM 名称")
    return llm


class CustomLLMChain:
    def __init__(self, **kwargs):
        self.temperature = kwargs.get("temperature", 0.1)
        self.llm = kwargs.get("llm", "zhipu")
        self.prompt = kwargs.get("prompt", None)
        self.memory = kwargs.get("memory", False)
        self.verbose = kwargs.get("verbose", True)
        if self.memory:
            config = iniconfig()
            self.connection_string = f"mongodb://{config[1]}:{urlquote(config[2])}@{config[0]}"
            self.database = config[3]

    def run(self, input: str, session_id: str = None, prompt = None, llm_model = None):
        prompt = prompt or self.prompt
        if prompt is None or prompt == "":
            raise ValueError("prompt is required")

        llm_model = llm_model or self.llm

        prompt_messages = [
            SystemMessagePromptTemplate.from_template(prompt),
            HumanMessagePromptTemplate.from_template("{question}")
        ]

        memory = None
        if self.memory:
            prompt_messages.append(MessagesPlaceholder(variable_name="chat_history"))
            if session_id is None or session_id == "":
                session_id = ''.join(random.sample(string.ascii_letters + string.digits, 32))
            memory = ConversationBufferMemory(
                input_key="question",
                output_key="text",
                return_messages=True,
                memory_key="chat_history",
                chat_memory=MongoDBChatMessageHistory(
                    connection_string=self.connection_string,
                    session_id=session_id,
                    collection_name="ai_kefu_history",
                    database_name=self.database,
                    history_size=5),
            )
        llm = get_support_llm(llm_model, temperature=self.temperature)
        prompt = ChatPromptTemplate(messages=prompt_messages)
        logging.info("Human: %s", input)
        conversation = LLMChain(
            llm=llm,
            prompt=prompt,
            memory=memory,
            verbose=self.verbose
        )
        try:
            output = conversation.invoke({"question": input})
            return output["text"]
        except RateLimitError as e:
            logging.error("Rate limit exceeded. Please try again later.")
            logging.exception(e)
            return "哎呀！你问的太快了，请等一等吧！"
        except AuthenticationError as e:
            logging.error("Authentication failed. Please check your API key.")
            logging.exception(e)
        except OpenAIError as e:
            logging.exception("An error occurred: %s", e)
        return "哎呀！我不知道怎么能回复你。"


class CustomLLMChainStream:
    def __init__(self, queue_manager: QueueManager, **kwargs):
        self.queue_manager = queue_manager
        self.temperature = kwargs.get("temperature", 0.1)
        self.llm = kwargs.get("llm", "zhipu")
        self.prompt = kwargs.get("prompt", None)
        self.memory = kwargs.get("memory", False)
        self.verbose = kwargs.get("verbose", True)
        if self.memory:
            config = iniconfig()
            self.connection_string = f"mongodb://{config[1]}:{urlquote(config[2])}@{config[0]}"
            self.database = config[3]

    def run(self, input: str, session_id: str = None, prompt = None, llm_model = None):
        prompt = prompt or self.prompt
        if prompt is None or prompt == "":
            raise ValueError("prompt is required")

        llm_model = llm_model or self.llm

        prompt_messages = [
            SystemMessagePromptTemplate.from_template(prompt),
            HumanMessagePromptTemplate.from_template("{question}")
        ]

        memory = None
        if self.memory:
            prompt_messages.append(MessagesPlaceholder(variable_name="chat_history"))
            if session_id is None or session_id == "":
                session_id = ''.join(random.sample(string.ascii_letters + string.digits, 32))
            memory = ConversationBufferMemory(
                input_key="question",
                output_key="text",
                return_messages=True,
                memory_key="chat_history",
                chat_memory=MongoDBChatMessageHistory(
                    connection_string=self.connection_string,
                    session_id=session_id,
                    collection_name="ai_kefu_history",
                    database_name=self.database,
                    history_size=5),
            )
        # 创建回调实例
        stream_handler = StreamResultCallbackHandler(self.queue_manager, session_id)
        llm = get_support_llm(llm_model, temperature=self.temperature,
                              # 启用流式模式
                              streaming=True,
                              # 传入回调处理器
                              callbacks=[stream_handler])
        prompt = ChatPromptTemplate(messages=prompt_messages)
        logging.info("Human: %s", input)
        conversation = LLMChain(
            llm=llm,
            prompt=prompt,
            memory=memory,
            verbose=self.verbose
        )
        try:
            output = conversation.invoke({"question": input})
            return output["text"]
        except RateLimitError as e:
            logging.error("Rate limit exceeded. Please try again later.")
            logging.exception(e)
            return "哎呀！你问的太快了，请等一等吧！"
        except AuthenticationError as e:
            logging.error("Authentication failed. Please check your API key.")
            logging.exception(e)
        except OpenAIError as e:
            logging.exception("An error occurred: %s", e)
        return "哎呀！我不知道怎么能回复你。"


# 自定义回调处理器
class StreamResultCallbackHandler(BaseCallbackHandler):
    def __init__(self, queue_manager, session_id):
        self.queue_manager = queue_manager
        self.tokens = []  # 用于存储流式生成的 token
        self.session_id = session_id
        # 用户提问的问题
        # self.question = question
        # self.status = 0
        self.queue = []
        self.queue_max_size = 6
        # 记录从初始化到结束所花费的时间
        self.init_time = time.time()
        self.start_time = time.time()
        self.end_time = time.time()
        self.begin_flag = False
        self.last_element = None

    def on_llm_new_token(self, token: str, **kwargs):
        """每生成一个新 token 时调用"""
        # 打印一下现在的时间
        if not self.begin_flag:
            logging.info("流式输出开始时间 Current time: %s", time.strftime("%H:%M:%S", time.localtime()))
            self.start_time = time.time()
            self.begin_flag = True
        self.tokens.append(token)
        token = filter_text(token)

        # 如何输出的token为空字符串，则忽略
        if token is None or token == "":
            return

        if (self.is_english_paragraph_end(token)
                or not self.is_english_paragraph_end(self.last_element)
                or len(self.queue) < self.queue_max_size):
            self.queue.append(token)
        else:
            self.queue_manager.put(self.session_id, "".join(self.queue))
            self.queue.clear()
            self.queue.append(token)

        self.last_element = token

    def on_llm_end(self, response, **kwargs):
        # 当流结束时触发
        logging.info(self.tokens)
        logging.info("Stream has finished.")
        self.queue_manager.put_end(self.session_id, "".join(self.queue))
        self.end_time = time.time()
        logging.info("总耗时-初始化到结束：%s", str(self.end_time - self.init_time))
        logging.info("总耗时：开始输出到结束：%s", str(self.end_time - self.start_time))

    def on_llm_error(self, error, **kwargs):
        # 当流报错时触发
        logging.error("on_llm_error An error occurred: %s", error)
        return_message = "哎呀！我不知道怎么能回复你。"
        if isinstance(error, RateLimitError):
            return_message = "哎呀！你问的太快了，请等一等吧！"
        if isinstance(error, AuthenticationError):
            logging.error("Authentication failed. Please check your API key.")
        self.queue_manager.put_error(self.session_id, 20008, return_message)

    def get_result(self) -> str:
        """获取完整生成结果"""
        return ''.join(self.tokens)

    @staticmethod
    def is_english_paragraph_end(text: str) -> bool:
        """判断是否是段落结束"""
        if not text:
            return False
        # 去除省略号的影响
        text = text.replace("...", "")
        # 兼容中文
        return ("." in text or ";" in text or "?" in text or "!" in text
                or "。" in text or "；" in text or "？" in text or "！" in text)


def iniconfig():
    hosts = config_manager.get_value("database.mongodb.hosts")
    user = config_manager.get_value("database.mongodb.user")
    passwd = config_manager.get_value("database.mongodb.password")
    database = config_manager.get_value("database.mongodb.database")
    return hosts, user, passwd, database

def is_emoji(char):
    # 获取字符的字节长度
    byte_length = len(char.encode('utf-8'))
    # 如果字节长度为 4，通常是表情符号
    if byte_length == 4:
        logging.warning(f"Found emoji:{char}")
        return True
    else:
        return False

def remove_emoji(text):
    """
    通过字节去除
    :param text:
    :return:
    """
    # 遍历每个字符，保留非表情符号的字符
    return ''.join([char for char in text if not is_emoji(char)])


def filter_text(text):
    """
    过滤
    :param text:
    :return:
    """
    logging.info("filter_text input text：%s", text)
    # 正则表达式匹配中文字符、英文字母、中文标点符号、英文标点符号以及空格
    pattern = re.compile(r'[^\u4e00-\u9fa5a-zA-Z0-9，。！？；：‘’“”【】（）《》、—…,.!?;:\'"`\[\]()<>/\-–~\s]')
    # 替换掉不符合条件的字符
    filtered_text = re.sub(pattern, '', text)
    logging.info("filter_text output text：%s", filtered_text)
    return filtered_text


if __name__ == '__main__':


    # chain = CustomLLMChain(prompt="""
    # 你是聊天助手
    # """, memory=True)
    # print(chain.run("hi", "aaaaaaaa"))
    # print(chain.run("hello", "aaaaaaaa"))

    q = QueueManager()
    chain = CustomLLMChainStream(queue_manager=q, prompt="""
    你是聊天助手
    """, memory=True, temperature=1.3)
    print(chain.run("hi", "aaaaaaaa"))
    # print(chain.run("hello", "aaaaaaaa"))

    sleep(3)
    print(q.get("aaaaaaaa"))
    # from suncodes_ai_chat.suncodes_document import doc_settings
    # from suncodes_ai_chat.suncodes_utils.file_base64 import read_file_content
    # prompt = read_file_content(doc_settings.PROMPT_QUESTION_LEVEL)
    # chain = CustomLLMChain(llm="zhipu", prompt=prompt, memory=False, temperature=1.3)
    # response = chain.run("li", "session_id")
    # print(response)
    # question_level = 0
    # if response == '1':
    #     question_level = 1
    # print(question_level)
