from enum import Enum

from suncodes_ai_chat.suncodes_document import doc_settings


class RoleAICodeEnum(Enum):
    BAIKE = (1, "百科小助手", doc_settings.PROMPT_BAIKE)
    TRANSLATE = (2, "翻译君", doc_settings.PROMPT_TEXT_TRANSLATE)

    def __init__(self, role_code, role_name, prompt_url):
        self.role_code = role_code
        self.role_name = role_name
        self.prompt_url = prompt_url

    @classmethod
    def get_enum_by_role_code(cls, role_code):
        # 遍历枚举成员，查找匹配的 role_code
        for role in cls:
            if role.role_code == role_code:
                return role
        raise ValueError(f"未找到 role_code 为 {role_code} 的枚举成员")
