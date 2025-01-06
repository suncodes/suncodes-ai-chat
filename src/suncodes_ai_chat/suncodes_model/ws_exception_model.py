from typing import Optional

from pydantic import BaseModel, Field


class BaseResponseModel(BaseModel):
    """基础响应"""
    status: Optional[int] = Field(200, title="HTTP状态码", description="HTTP状态码，和HTTP状态码的含义一样")
    code: Optional[int] = Field(None, title="自定义业务异常编码", description="自定义业务异常编码")
    message: Optional[str] = Field(None, title="异常信息", description="异常信息")
