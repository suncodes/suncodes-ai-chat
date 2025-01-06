"""
websocket 管理
"""
import logging

from fastapi import WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)

# 存储 WebSocket 连接与 sessionId 的映射
active_connections = {}

def add_connection(session_id: str, websocket: WebSocket):
    """
    添加连接
    :param session_id:
    :param websocket:
    :return:
    """
    active_connections[session_id] = websocket

def remove_connection(session_id: str):
    """
    移除连接
    :param session_id:
    :return:
    """
    logger.info("从连接池中移除连接 %s", session_id)
    if session_id not in active_connections:
        return
    del active_connections[session_id]

async def close_connection(session_id: str):
    """
    关闭连接，同时会移除缓存
    :param session_id:
    :return:
    """
    if session_id in active_connections:
        websocket = active_connections[session_id]
        try:
            await websocket.close()
        except WebSocketDisconnect:
            pass
        remove_connection(session_id)

async def send_message_to_session(sessionId: str, message: str):
    """
    向指定 sessionId 的客户端发送消息
    :param sessionId:
    :param message:
    :return:
    """
    try:
        if sessionId in active_connections:
            websocket = active_connections[sessionId]
            await websocket.send_text(message)
            # 如何不为空，则截断，如果为空，则不截断
            print_message = message
            if message is not None:
                print_message = message[:300]
            logger.info("消息推送给 %s: %s", sessionId, print_message)
        else:
            logger.warning("没有找到客户端 %s", sessionId)
    except Exception as e:
        logger.warning("客户端 %s 已断开连接", sessionId)
        logger.exception(e)
        # 移除断开的连接
        remove_connection(sessionId)

async def send_message_to_session_and_close(sessionId: str, message: str):
    """ 向指定 sessionId 的客户端发送消息，发送完并且关闭 websocket """
    await send_message_to_session(sessionId, message)
    await close_connection(sessionId)

async def receive_message_from_session(sessionId: str, callback_function):
    """
    接收用户数据，并回调
    :param sessionId: 会话id
    :param callback_function: 回调函数
    :param kwargs: 回调函数的字典参数
    :return:
    """
    websocket = active_connections[sessionId]
    try:
        while True:
            # 接收客户端消息
            data = await websocket.receive_text()
            logger.info("收到客户端 %s 消息: %s", sessionId, data)
            # 回复客户端
            await callback_function(sessionId, data)
            # close_connection(sessionId)
    except WebSocketDisconnect:
        logger.warning("客户端 %s 断开连接", sessionId)
        # 移除断开的连接
        remove_connection(sessionId)
