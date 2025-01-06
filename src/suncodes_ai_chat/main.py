"""
这是一个 FastAPI 应用程序，提供英语聊天和每日问答的 API 接口。
加载日志配置并启动 uvicorn 服务器以运行应用程序。
"""

import logging

import uvicorn
from fastapi import FastAPI

from suncodes_ai_chat.suncodes_config.config_logging import load_logging_dict_config, config_logging

logging = logging.getLogger(__name__)
# 加载日志配置
dict_config = load_logging_dict_config()
config_logging(dict_config=dict_config)

app = FastAPI()


def start():
    """
    启动入口
    """
    # 启动 uvicorn
    uvicorn.run(
        app,  # 替换为你的 FastAPI 或 ASGI 应用
        host="0.0.0.0",
        port=8080,
        log_level="info",  # 设置日志级别
        access_log=True,  # 启用访问日志
        log_config=dict_config,  # 设置日志配置（覆盖原有配置）
    )


if __name__ == "__main__":
    start()
