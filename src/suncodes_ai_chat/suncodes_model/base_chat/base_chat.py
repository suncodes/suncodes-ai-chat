from typing import Optional

from pydantic import BaseModel, Field
from suncodes_ai_chat.suncodes_model.ws_exception_model import BaseResponseModel


class BaseAskQuery(BaseModel):
    """语音：请求参数"""
    roleCode: int = Field(None, title="AI角色编码", description="AI角色编码")
    userAudioUrl: str = Field(None, title="用户语音URL", description="用户语音URL")
    sessionId: str = Field(None, title="会话ID", description="会话ID")


class BaseTextAskQuery(BaseModel):
    """文本：请求参数"""
    roleCode: int = Field(None, title="AI角色编码", description="AI角色编码")
    text: str = Field(None, title="用户文本", description="用户文本")
    sessionId: str = Field(None, title="会话ID", description="会话ID")


class BaseAskVO(BaseModel):
    """文本：请求参数"""
    myselfText: str = Field(None, title="用户文本", description="用户文本")
    speechText: str = Field(None, title="AI回答文本", description="AI回答的文本，即响应语音对应的文本内容")
    speech: str = Field(None, title="响应语音的URL", description="响应语音的UR，经历AI回答后，通过tts生成的语音地址")
    time: int = Field(None, title="响应语音时长", description="响应语音时长，单位为秒（s）")


class WsAskVO(BaseResponseModel):
    """
            result = {
                "type": 2,
                "myselfText": None,
                "speech": None,
                "time": None,
                "speechText": data,
                "textSeq": self.seqs[session_id],
                "status": 1,
                "audio": None,
                "audioSeq": int(math.ceil(self.seqs[session_id] / self.merge_chunk))
            }
    """
    type: int = Field(None, title="消息类型", description="消息类型，1：语音转文本消息；2：LLM文本消息，3语音base64消息")
    streamStatus: int = Field(None, title="状态", description="状态，1：进行中 2：结束")
    myselfText: str = Field(None, title="用户文本", description="用户文本")

    speechText: str = Field(None, title="AI回答文本", description="AI回答的文本，即响应语音对应的文本内容")
    textSeq: int = Field(None, title="文本序号", description="文本序号，用于标识当前文本的序号，与AI文本配合使用")

    audio: str = Field(None, title="音频base64", description="音频base64，AI回答的答案，通过tts合成")
    audioSeq: int = Field(None, title="音频序号", description="音频序号，用于标识当前音频的序号，与AI语音配合使用")

    speech: str = Field(None, title="响应语音的URL", description="响应语音的UR，经历AI回答后，通过tts生成的语音地址")
    time: int = Field(None, title="响应语音时长", description="响应语音时长，单位为秒（s）")
    chatId: str = Field(None, title="对话记录主键ID", description="对话记录主键ID")


class StreamCacheModel(BaseResponseModel):
    """
    缓存数据
    """
    roleCode: Optional[int] = Field(None, title="AI角色编码", description="AI角色编码")
    userAudioUrl: Optional[str] = Field(None, title="用户语音URL", description="用户语音URL")
    sessionId: Optional[str] = Field(None, title="会话ID", description="会话ID")
    chatId: Optional[str] = Field(None, title="对话记录主键ID", description="对话记录主键ID")
    question: Optional[str] = Field(None, title="问题", description="问题")
    answer: Optional[str] = Field(None, title="AI回答", description="AI回答")
    answerAudioUrl: Optional[str] = Field(None, title="AI回答语音URL", description="AI回答语音URL")
    streamStatus: Optional[int] = Field(None, title="状态", description="状态，1：进行中 2：结束")
