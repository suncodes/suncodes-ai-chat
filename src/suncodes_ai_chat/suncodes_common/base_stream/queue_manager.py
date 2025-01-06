import queue
import threading


class QueueManager:
    """
    队列管理器，管理与 session_id 相关的数据队列，并支持在队列数据到达时触发回调事件。
    """

    def __init__(self):
        # 存储每个 session_id 对应的队列
        self.queues = {}
        self.first_flags = {}
        # 用于保护队列操作的锁
        self.lock = threading.Lock()
        # 定义回调函数列表
        self.callbacks = []

    def _get_or_create_queue(self, session_id: str) -> queue.Queue:
        """获取或创建一个新的队列"""
        with self.lock:
            if session_id not in self.queues:
                self.queues[session_id] = queue.Queue()
        return self.queues[session_id]

    def put(self, session_id: str, data: str):
        """
        向队列中放入数据，并触发相应的回调事件。

        :param session_id: 当前会话 ID，标识队列
        :param data: 要放入队列的数据
        :param on_first_data: 数据第一次到达队列时的回调函数
        :param on_last_data: 数据最后写入时的回调函数
        """
        queue = self._get_or_create_queue(session_id)
        # 放入数据
        queue.put(data)
        if (session_id not in self.first_flags) or (not self.first_flags[session_id]):
            self.first_flags[session_id] = True
            self.on_data_chunk(data, session_id, 0)
        else:
            self.on_data_chunk(data, session_id, 1)

    def put_end(self, session_id: str, data: str):
        """
        向队列中放入数据，并触发相应的回调事件。

        :param session_id: 当前会话 ID，标识队列
        :param data: 要放入队列的数据
        :param on_first_data: 数据第一次到达队列时的回调函数
        :param on_last_data: 数据最后写入时的回调函数
        """
        queue = self._get_or_create_queue(session_id)
        # 放入数据
        queue.put(data)
        self.first_flags[session_id] = False
        self.on_data_chunk(data, session_id, 2)
        self.on_data_end(session_id)

    def put_error(self, session_id: str, error_code: int, reason: str):
        """
        流错误
        :param session_id:
        :param error_code:
        :param reason:
        :return:
        """
        self.on_data_error(session_id, error_code, reason)

    def get(self, session_id: str) -> str:
        """
        从队列中取出数据。

        :param session_id: 当前会话 ID，标识队列
        :return: 队列中的数据
        """
        queue = self._get_or_create_queue(session_id)
        if queue.empty():
            raise IndexError(f"Queue for session {session_id} is empty.")
        return queue.get()

    def on_data_chunk(self, data, session_id: str, status: int):
        """
        当队列中的数据到达时，触发相应的回调事件。
        注意：此处不需要或者不准从队列中取数据，否则后续 on_data_end 有问题。
        :param data: 当前的数据
        :param session_id: 当前的会话
        :param status: 当前的状态
        """
        for callback in self.callbacks:
            callback(data, session_id, status)
        pass

    def add_callback(self, callback):
        """
        添加回调函数
        """
        self.callbacks.append(callback)
        pass

    def on_data_end(self, session_id: str):
        """
        当最后的数据到达时，进行的函数回调
        :param session_id: 当前的会话
        """
        pass

    def on_data_error(self, session_id: str, error_code: int, reason: str):
        """
        流错误
        :param session_id:
        :param error_code:
        :param reason:
        :return:
        """
        pass

def f(session_id: str, status: int):
    print(f"Session {session_id}: Data chunk {status}.")

# class QueueManagerHandler:
#     def __init__(self, queue_manager: QueueManager):
#         self.queue_manager = queue_manager
#         self.bind()
#
#     def bind(self):
#         self.queue_manager.on_data_chunk = self.on_data_chunk
#         pass
#
#     def on_data_chunk(self, session_id: str, status: int):
#         print(f"Session {session_id}: Data chunk {status}.")
#         pass


# 测试
def test_queue_manager():
    queue_manager = QueueManager()
    # queue_manager_handler = QueueManagerHandler(queue_manager)

    queue_manager.on_data_chunk = f

    # 假设有两个 session_id
    session_1 = "session_1"
    session_2 = "session_2"

    # 向 session_1 队列中放入数据
    queue_manager.put(session_1, "data_1")
    queue_manager.put(session_1, "data_2")
    queue_manager.put_end(session_1, "data_3")
    queue_manager.put(session_1, "data_4")

    # 向 session_2 队列中放入数据
    queue_manager.put(session_2, "data_1")

    # 从队列中取数据
    print(queue_manager.get(session_1))  # 输出: data_1
    print(queue_manager.get(session_1))  # 输出: data_2

if __name__ == "__main__":
    test_queue_manager()
