import base64

import chardet
from mutagen.mp3 import MP3


# 根据 Base64 字符串获取文件字节数
def get_file_size_from_base64(base64_str):
    # 解码 Base64 字符串
    decoded_data = base64.b64decode(base64_str)
    # 获取解码后的字节数
    file_size = len(decoded_data)
    return file_size

def get_mp3_duration(mp3_bytes):
    # 将字节流数据加载到 BytesIO 中
    from io import BytesIO
    mp3_file = BytesIO(mp3_bytes)

    # 判断文件大小，如果为空，则直接返回0
    if not mp3_bytes or len(mp3_bytes) == 0:
        return 0
    # 使用 mutagen 解析字节流
    audio = MP3(fileobj=mp3_file)
    # 获取音频时长，单位为秒
    duration = audio.info.length
    # 取整数
    return int(duration)

def read_file_content(file_path: str) -> str:
    with open(file_path, "rb") as f:
        raw_data = f.read()
        result = chardet.detect(raw_data)
        encoding = result["encoding"]

        if encoding in ["Windows-1252", "Windows-1254", "MacRoman"]:
            encoding = "utf-8"

    with open(file_path, "r", encoding=encoding) as f:
        return f.read()
