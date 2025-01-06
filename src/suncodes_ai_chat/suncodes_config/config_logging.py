import json
import logging
import logging.config
import os
import socket

import yaml

from suncodes_ai_chat.suncodes_config.config_manager import (config_manager,
                                                   config_settings)


def load_logging_dict_config():
    """
    获取日志dict配置
    :return:
    """
    hostname = socket.gethostname()
    application_name = config_settings.APPLICATION_NAME

    config = config_manager.get_value("logging")
    config_content = json.dumps(config)

    config_content = (config_content
                      .replace('__application_name__', application_name)
                      .replace('__application_instance_name__', hostname))
    # 加载 YAML 配置内容
    config = yaml.safe_load(config_content)

    try:
        filename = config_settings.get_key_in_config(config, "handlers.file_handler.filename")
        # 自动创建日志文件目录，否则会报错
        log_dir = os.path.dirname(filename)
        if not os.path.exists(log_dir):
            os.mkdir(log_dir)
    except KeyError:
        pass
    except Exception as e:
        print(e)
    try:
        filename = config_settings.get_key_in_config(config, "handlers.file_size_handler.filename")
        # 自动创建日志文件目录，否则会报错
        log_dir = os.path.dirname(filename)
        if not os.path.exists(log_dir):
            os.mkdir(log_dir)
    except KeyError:
        pass
    except Exception as e:
        print(e)
    return config


def config_logging(dict_config: dict):
    """
    配置日志
    :param dict_config: dict 参数
    :return:
    """
    if dict_config is None:
        logging.config.dictConfig(load_logging_dict_config())
    else:
        logging.config.dictConfig(dict_config)

# # https://pyloong.github.io/pythonic-project-guidelines/guidelines/advanced/logging/#21-ini
# # https://juejin.cn/post/6966998948531666981
