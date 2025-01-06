"""
在流进行滚动过程中，会产生一些全局的数据，可能在某些流程中会用到
作用：提供一个内存存储的地方，通过session_id，可以查询，写入一些公共数据
"""
import json
import logging

logging = logging.getLogger(__name__)


class StreamCacheManager:
    def __init__(self):
        self.data_map = {}

    def get_data(self, session_id: str) -> str:
        if session_id in self.data_map:
            return self.data_map[session_id]
        else:
            return json.dumps({})

    def set_data(self, session_id: str, data: str):
        self.data_map[session_id] = data
        pass

    def remove_data(self, session_id: str):
        if session_id in self.data_map:
            del self.data_map[session_id]
        pass
