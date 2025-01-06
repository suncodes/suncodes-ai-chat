import asyncio
import inspect
import json
import logging
from abc import ABC

from suncodes_ai_chat.suncodes_common.base_stream.queue_manager import QueueManager


def before_call_check_error(func):
    """
    装饰器：用于在每个所注解的方法，在方法前执行一段自定义逻辑
    逻辑需要自己重写 on_before_check_error 方法进行实现
    :param func:
    :return:
    """
    def wrapper(*args, **kwargs):
        """
        *args: 数组类型的参数，a=1, b=2, c=3
        **kwargs：dict类型的参数 {d:4, e:5}
        """
        # 获取函数签名
        signature = inspect.signature(func)
        # 获取参数名
        parameters = signature.parameters
        param_names = list(parameters.keys())
        # 打印参数名和它们的值
        logging.debug("Before calling %s", func.__name__)

        my_class = None
        session_id = None
        for i, param_name in enumerate(param_names):
            if i < len(args):
                # logging.debug(f"{param_name}: {args[i]}")
                if param_name == "self":
                    my_class = args[i]
                if param_name == "session_id":
                    session_id = args[i]
            elif param_name in kwargs:
                # logging.debug(f"{param_name}: {kwargs[param_name]}")
                if param_name == "self":
                    my_class = kwargs[param_name]
                if param_name == "session_id":
                    session_id = kwargs[param_name]
            else:
                logging.warning("%s: not provided", param_name)
        if my_class is not None and session_id is not None and my_class.cache_manager is not None:
            common_data = my_class.cache_manager.get_data(session_id)
            common_data = json.loads(common_data)
            status = common_data.get("status", 1)
            if status == 0:
                logging.error("%s 通过拦截发现流出现了异常情况，此时需要截断流，目前方法名：%s，所在类：%s",
                              session_id, func.__name__, my_class.__class__.__name__)
                my_class.on_before_check_error(session_id)
                return None
        return func(*args, **kwargs)
    return wrapper


class StreamHandler(ABC):
    def __init__(self, input_queue_manager: QueueManager, output_queue_manager: QueueManager):
        """
        param: input_queue_manager: 输入流，Handler 监听的就是输入流的事件
        param: output_queue_manager:输出流，即自己产生的流数据，on_self_stream_chunk 可以监听自己的流事件。
               在 xxx_chunk() 中不能对input_queue_manager进行读写操作，否则会影响on_stream_end
        """
        self.input_queue_manager = input_queue_manager
        self.output_queue_manager = output_queue_manager
        if input_queue_manager is not None:
            self.input_queue_manager.add_callback(self.on_stream_chunk)
            self.input_queue_manager.on_data_end = self.on_stream_end
            self.input_queue_manager.on_data_error = self.on_stream_error
        if output_queue_manager is not None:
            self.output_queue_manager.add_callback(self.on_self_stream_chunk)
        self.cache_manager = None

    @before_call_check_error
    def on_stream_start(self, session_id: str):
        """
        初始化
        """
        pass

    @before_call_check_error
    def on_stream_chunk(self, data:str, session_id: str, status: int):
        """
        处理数据
        """
        pass

    @before_call_check_error
    def on_stream_end(self, session_id: str):
        """
        结束
        """
        # 获取所有数据（相当于清空队列）
        while not self.input_queue_manager.queues[session_id].empty():
            self.input_queue_manager.get(session_id)
        pass

    @before_call_check_error
    def on_stream_error(self, session_id: str, error_code: int, reason: str):
        """
        流出现了异常
        """
        pass

    @before_call_check_error
    def on_self_stream_chunk(self, data:str, session_id: str, status: int):
        """
        结束
        """
        pass

    def on_before_check_error(self, session_id: str):
        """
        开始之前检查流是否错误
        """
        pass

# 判断当前事件循环是否运行
def is_event_loop_running():
    try:
        # 获取当前事件循环
        loop = asyncio.get_event_loop()
        # 检查事件循环是否已经运行
        return loop.is_running()
    except RuntimeError:
        # 如果没有事件循环，则说明没有运行中的事件循环
        return False
    pass

