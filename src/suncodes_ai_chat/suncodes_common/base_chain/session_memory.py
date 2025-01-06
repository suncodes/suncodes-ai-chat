from collections import deque
from datetime import datetime, timedelta
from typing import Any

from langchain.memory import ConversationBufferMemory


class MultiSessionConversationBufferMemory(ConversationBufferMemory):
    buffer_size: int = 5  # buffer_size 类型注解
    sessions: dict = {}
    max_sessions: int = 100  # 最大 session 数

    def _get_session_memory(self, session_id):
        """Retrieve or create memory for a session."""
        self._clear_inactive_sessions()

        if session_id not in self.sessions:
            # 如果 sessions 数量超出限制，移除最早的 session
            if len(self.sessions) >= self.max_sessions:
                self._remove_oldest_session()

            # 创建一个新的 deque 存储会话信息，最大长度为 buffer_size
            self.sessions[session_id] = {
                "memory": deque(maxlen=self.buffer_size),
                "last_active": datetime.now()
            }
        else:
            # 更新最后活动时间
            self.sessions[session_id]["last_active"] = datetime.now()

        return self.sessions[session_id]["memory"]

    def _remove_oldest_session(self):
        """移除最早的 session"""
        oldest_session = min(self.sessions, key=lambda s: self.sessions[s]["last_active"])
        del self.sessions[oldest_session]

    def _clear_inactive_sessions(self):
        """清除超过2小时不活跃的 session"""
        now = datetime.now()
        inactive_sessions = [session_id for session_id, session_data in self.sessions.items()
                             if now - session_data["last_active"] > timedelta(hours=2)]
        for session_id in inactive_sessions:
            del self.sessions[session_id]

    def add_message(self, session_id, message):
        """向指定 session 添加消息"""
        session_memory = self._get_session_memory(session_id)
        session_memory.append(message)

    def get_memory(self, session_id):
        """获取指定 session 的会话内容"""
        session_memory = self._get_session_memory(session_id)
        return list(session_memory)

    def clear_memory(self, session_id):
        """清除指定 session 的会话内容"""
        if session_id in self.sessions:
            del self.sessions[session_id]

    def load_memory_variables(self, inputs, session_id=None):
        """
        Override to support retrieving memory variables for a specific session.
        :param inputs: Inputs passed to the memory (can be ignored here).
        :param session_id: The session_id for which memory is to be loaded.
        """
        if session_id is None:
            raise ValueError("session_id must be provided to load memory.")
        session_memory = self._get_session_memory(session_id)
        return list(session_memory)


# # Example usage:
# memory = MultiSessionConversationBufferMemory(buffer_size=3)
# memory.add_message("123", "Hello!")
# memory.add_message("123", "How are you?")
# print(memory.get_memory("123"))  # Output: ['Hello!', 'How are you?']
# memory.add_message("123", "What's the weather?")
# print(memory.get_memory("123"))  # Output: ['How are you?', "What's the weather?"]
# memory.add_message("456", "Hi there!")
# print(memory.get_memory("456"))  # Output: ['Hi there!']
# memory.clear_memory("123")
# print(memory.get_memory("123"))  # Output: []
# memory_vars = memory.load_memory_variables({}, session_id="456")
# print(memory_vars)  # Output: {'history': ['Hi there!']}
