"""
自定义异常业务类，以及对应的处理器
"""
import logging
from fastapi import WebSocket

from suncodes_ai_chat.suncodes_model.ws_exception_model import BaseResponseModel

logger = logging.getLogger(__name__)

# 通用提示语
_default_error_messages = {
    '400': '权限异常',
    '401': '参数异常',
    '404': '接口不存在',
    '500': '服务端程序异常',
}


async def websocket_handle_exception(request: WebSocket, e: Exception):
    """
    处理其他异常
    :param request:
    :param e:
    :return:
    """
    ret = BaseResponseModel(status=500, code=0, message=_default_error_messages.get('500'))
    logger.exception('websocket_handle_exception, 异常详情: %s', e)
    await request.send_text(ret.model_dump_json())
    # 关闭 WebSocket 连接
    await request.close(code=3000, reason=ret.model_dump_json())


async def websocket_exception_handler(websocket: WebSocket):
    """
    websocket 异常处理
    :param websocket:
    :return:
    """
    try:
        yield
    except Exception as e:
        await websocket_handle_exception(websocket, e)

# from fastapi import FastAPI, WebSocket, HTTPException
# from fastapi.exceptions import RequestValidationError
# from pydantic import ValidationError
# app.add_exception_handler(RequestValidationError, handle_validation_exception)
# app.add_exception_handler(ValidationError, handle_validation_exception)
# app.add_exception_handler(HTTPException, handle_http_exception)
# app.add_exception_handler(XxtBaseException, handle_suncodes_base_exception)
# app.add_exception_handler(Exception, handle_exception)
