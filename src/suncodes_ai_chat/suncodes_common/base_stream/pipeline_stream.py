from suncodes_ai_chat.suncodes_common.base_stream.stream_cache_manager import \
    StreamCacheManager
from suncodes_ai_chat.suncodes_common.base_stream.stream_handler import StreamHandler


class PipelineStream:
    """
    流式处理，组合多个 PipelineStreamHandler，进行一级一级的流式传递
    """
    def __init__(self, handlers: list[StreamHandler], cache: bool = False):
        self.handlers = handlers
        self.cache_manager = None
        if cache:
            self.cache_manager = StreamCacheManager()

    def start(self, session_id: str):
        for handler in self.handlers:
            handler.cache_manager = self.cache_manager
            handler.on_stream_start(session_id)
        return self

    def pipeline(self, session_id: str, data: str):
        # 获取第一个 handler, 并判断是否为 InputHandler
        handler = self.handlers[0]
        # from src.tts.core.stream_handler import InputHandler
        # if not isinstance(handler, InputHandler):
        #     raise Exception("第一个 handler 必须为 InputHandler")
        handler.input_queue_manager.put_end(session_id, data)
        return self
