from enum import Enum


class ErrorStatusEnum(Enum):
    INPUT_TEXT = (10001, "输入文本错误")
    NO_SPEAK = (10002, "没有说话")
    SPEECH_FAIL = (20003, "语音识别失败")
    PROMPT_FAIL = (20004, "提示语失败")
    CREATE_CHAT_FAIL = (20005, "创建对话失败")
    UPDATE_CHAT_FAIL = (20006, "更新对话失败")
    UPDATE_DAILY_LIMIT_FAIL = (20007, "更新每日对话次数失败")
    LLM_RESPONSE_FAIL = (20008, "LLM 响应失败")

    def __init__(self, error_code, error_desc):
        self.error_code = error_code
        self.error_desc = error_desc
