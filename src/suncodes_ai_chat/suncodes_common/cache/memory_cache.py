"""
内存缓存，仅存在内存中，并不进行持久化
"""
class MemoryCache:
    """ 内存缓存 """

    def __init__(self):
        self.cache = {}

    def add_cache(self, key: str, value: any):
        """
        添加缓存
        :param key:
        :param value:
        :return:
        """
        self.cache[key] = value

    def get_cache(self, key: str) -> any:
        """
        获取缓存的值
        :param key:
        :return:
        """
        return self.cache.get(key)

    def remove_cache(self, key: str):
        """
        移除缓存
        :param key:
        :return:
        """
        self.cache.pop(key)

    def clear_cache(self):
        """
        清除缓存（所有）
        :return:
        """
        self.cache.clear()

    def exists_key(self, key: str) -> bool:
        """
        key是否存在缓存中
        :param key:
        :return:
        """
        return key in self.cache


memory_cache: MemoryCache = MemoryCache()
__all__ = [memory_cache]
