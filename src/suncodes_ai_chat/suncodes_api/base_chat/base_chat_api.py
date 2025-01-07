"""
聊天 API
"""
import logging

from fastapi import APIRouter, Query, Body, WebSocket, Depends

from suncodes_ai_chat.suncodes_app.base_chat.base_chat import (ai_chat_stream, ai_chat_text_stream, base_ask,
                                                               base_text_ask)
from suncodes_ai_chat.suncodes_model.base_chat.base_chat import (BaseAskQuery, BaseTextAskQuery, BaseAskVO)
from suncodes_ai_chat.suncodes_common.websocket_pool.websocket_manager import (
    add_connection, receive_message_from_session)
from suncodes_ai_chat.suncodes_config.config_exception import websocket_exception_handler

logging = logging.getLogger(__name__)

router = APIRouter(prefix="/base-chat", tags=["AI对话"])


@router.websocket("/stream-ask", dependencies=[Depends(websocket_exception_handler)])
async def websocket_ask(websocket: WebSocket, sessionId: str = Query(...)):
    """WebSocket 连接，并与 sessionId 绑定"""
    await websocket.accept()
    # 将 sessionId 与 websocket 连接绑定
    add_connection(sessionId, websocket)
    logging.info("客户端 %s 已连接", sessionId)

    await receive_message_from_session(sessionId, ai_chat_stream)


@router.websocket("/stream-text-ask", dependencies=[Depends(websocket_exception_handler)])
async def websocket_text_ask(websocket: WebSocket, sessionId: str = Query(...)):
    """WebSocket 连接，并与 sessionId 绑定"""
    await websocket.accept()
    # 将 sessionId 与 websocket 连接绑定
    add_connection(sessionId, websocket)
    logging.info("客户端 %s 已连接", sessionId)

    await receive_message_from_session(sessionId, ai_chat_text_stream)


@router.post("/ask", response_model=BaseAskVO)
async def api_ask(item: BaseAskQuery = Body(...)):
    """HTTP ASK"""
    return await base_ask(item)


@router.post("/text-ask")
async def api_text_ask(item: BaseTextAskQuery = Body(...)):
    """HTTP TEXT ASK"""
    return await base_text_ask(item)
