from pathlib import Path
from typing import Dict, List

from pip._vendor import tomli

# 项目根目录
BASE_DIR = Path(__file__).resolve().parent


def load_env_config_content(env_profile):
    config_path = CONFIG_PATH / f"{env_profile}.yml"
    with open(config_path, 'r', encoding='utf-8') as f:
        return f.read()


def find_project_root(path: Path, marker_files=None) -> Path:
    if marker_files is None:
        marker_files = ["pyproject.toml"]
    for parent in path.parents:
        for marker in marker_files:
            if (parent / marker).exists():
                return parent
    return path


def get_pyproject_value(key: str):
    """
    从 pyproject.toml 文件中获取指定 key 的值
    :param key:
    :return:
    """
    if PYPROJECT_TOML_PATH is None:
        project_root = find_project_root(Path(__file__))
        pyproject_path = project_root / PYPROJECT_TOML
    else:
        pyproject_path = PYPROJECT_TOML_PATH
    if not pyproject_path.exists():
        raise FileNotFoundError(f"未找到 {PYPROJECT_TOML} 文件")
    with open(pyproject_path, "rb") as f:
        data = tomli.load(f)
        return get_key_in_config(data, key)


def get_key_in_config(root: Dict, key: str):
    """
    递归搜索，检查字典路径是否存在
    """
    key_list = key.split(".")
    return __get_key_in_config(root, key_list, 0)


def __get_key_in_config(root: Dict, key_list: List[str], ind: int):
    """
    递归搜索，检查字典路径是否存在
    """
    if ind >= len(key_list):
        raise KeyError(f"索引 {ind} 超出关键字列表长度")

    if key_list[ind] not in root:
        raise KeyError(f"关键字 {key_list[ind]} 不存在于配置文件中")

    elif isinstance(root[key_list[ind]], dict):
        if ind == len(key_list) - 1:
            # 关键字存在，且是字典，到达终止条件，终止并返回
            return root[key_list[ind]]
        # 关键字存在，且是字典，则继续递归
        return __get_key_in_config(root[key_list[ind]], key_list, ind + 1)
    else:
        # 关键字存在，且不是字典，则返回值
        return root[key_list[ind]]


PYPROJECT_TOML = "pyproject.toml"
PYPROJECT_TOML_PATH = find_project_root(Path(__file__)) / PYPROJECT_TOML
APPLICATION_NAME = get_pyproject_value("tool.poetry.name").replace("suncodes-", "")

# 配置文件路径（目前是本地文件，后续可改为http://config）
CONFIG_PATH = BASE_DIR

if __name__ == '__main__':
    import sys

    python_path = sys.executable
    print(f"Python解释器路径: {python_path}")
    print(f"Python sys.path 路径: {sys.path}")
    print(get_pyproject_value("tool.poetry.name"))
