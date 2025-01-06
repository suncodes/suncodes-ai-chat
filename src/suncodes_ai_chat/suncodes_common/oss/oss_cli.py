import base64
import datetime
import logging
import time
from urllib.parse import urlparse

import boto3

from suncodes_ai_chat.suncodes_config.config_manager import config_manager
from suncodes_ai_chat.suncodes_utils.random_string import generate_random_string


class CustomOSSClient:
    def __init__(self):
        aws_access_key_id, aws_secret_access_key, endpoint_url, bucket_name = self.__iniconfig()
        self.access_key_id = aws_access_key_id
        self.access_key_secret = aws_secret_access_key
        self.endpoint = endpoint_url
        self.bucket_name = bucket_name

    def get_client(self):
        return boto3.client(
            service_name='s3',
            aws_access_key_id=self.access_key_id,
            aws_secret_access_key=self.access_key_secret,
            endpoint_url=self.endpoint
        )

    def upload_file_random_path(self, bytes_content, file_suffix_no_dot="mp3") -> str:
        file_name = str(int(round(time.time() * 1000))) + "-" + generate_random_string(6)
        today = datetime.datetime.today()
        year = today.year
        month = today.month
        # 在 S3 中的存储路径
        object_name = f"{year}{month}/{file_name}.{file_suffix_no_dot}"
        return self.upload_file(object_name, bytes_content)

    def upload_file(self, file_path, bytes_content) -> str:
        s3_client = self.get_client()
        try:
            # 上传文件
            s3_client.put_object(
                Bucket=self.bucket_name,
                Key=file_path,
                Body=bytes_content,
                ContentType='application/octet-stream'  # 根据实际文件类型修改
            )
            logging.info(f"文件已成功上传到 S3 桶 {self.bucket_name}，路径为 {file_path}")
            address = f'{self.endpoint}/{self.bucket_name}/{file_path}'
            return address
        except Exception as e:
            logging.error(f"上传时发生错误: {e}")
        pass

    def download_file(self, url):
        bucket_name, s3_key = self.parse_s3_url(url)
        # 创建 S3 客户端并传递凭证和区域
        s3_client = self.get_client()
        try:
            # 获取文件对象
            response = s3_client.get_object(Bucket=bucket_name, Key=s3_key)
            # 获取文件内容
            file_content = response['Body'].read()  # 读取文件字节流
            logging.info(f"文件内容：{file_content[:100]}...")  # 打印文件的前100字节
            return file_content
        except Exception as e:
            logging.error(f"获取文件失败: {e}")
        pass

    def download_base64_file(self, url):
        bytes_content = self.download_file(url)
        return base64.b64encode(bytes_content).decode('utf-8')

    @staticmethod
    def parse_s3_url(url):
        # 使用 urlparse 解析 URL
        parsed_url = urlparse(url)

        # 提取 bucket_name 和 key
        path_parts = parsed_url.path.lstrip('/').split('/', 1)

        if len(path_parts) == 2:
            bucket_name = path_parts[0]
            key = path_parts[1]
            return bucket_name, key
        else:
            raise ValueError("Invalid S3 URL format")

    @staticmethod
    def __iniconfig():
        aws_access_key_id = config_manager.get_value("oss.aws_access_key_id")
        aws_secret_access_key = config_manager.get_value("oss.aws_secret_access_key")
        endpoint_url = config_manager.get_value("oss.endpoint_url")
        bucket_name = config_manager.get_value("oss.bucket_name")
        return aws_access_key_id, aws_secret_access_key, endpoint_url, bucket_name
