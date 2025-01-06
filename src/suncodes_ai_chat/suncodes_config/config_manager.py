from copy import deepcopy

import yaml

from suncodes_ai_chat.suncodes_config import config_settings
from suncodes_ai_chat.suncodes_config.env import ENV


def deep_merge_dict(x, y):
    """
    深合并字典
    :param x:
    :param y:
    :return:
    """
    if x is None:
        return y
    if y is None:
        return x
    z = deepcopy(x)
    z.update(y)
    for k, v in z.items():
        if k in x and k in y:
            if isinstance(x[k], dict) and isinstance(y[k], dict):
                z[k] = deep_merge_dict(x[k], y[k])
    return z


class ConfigManager:
    """
    配置文件管理器
    """

    def __init__(self):
        self.config_content = None
        self.config_path = None
        self.env = ENV
        self.load_file()

    def load_file(self):
        self.config_path = f'{config_settings.APPLICATION_NAME}-{self.env}'
        try:
            # 读取基础配置文件
            content = config_settings.load_env_config_content(config_settings.APPLICATION_NAME)
            self.config_content = yaml.load(content, Loader=yaml.FullLoader)
            patch_config = yaml.load(config_settings.load_env_config_content(self.config_path), Loader=yaml.FullLoader)
        except Exception as e:
            raise IOError(f"配置文件读取失败，路径: {self.config_path}")

        self.config_content = deep_merge_dict(self.config_content, patch_config)

    def get_value(self, key: str) -> any:
        """
        获取配置文件中的值
        key : tool.poetry.name
        """
        if self.config_content is None:
            return IOError("配置文件未加载")
        return config_settings.get_key_in_config(self.config_content, key)


config_manager: ConfigManager = ConfigManager()
__all__ = [config_manager]
