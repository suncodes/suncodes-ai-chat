from typing import Any

from langchain_openai import ChatOpenAI

from suncodes_ai_chat.suncodes_constants import zhipu_constants


class ZhipuAILLM(ChatOpenAI):
    """
    ZhipuAILLM: A class for interacting with the ZhipuAI API.
    """

    def __init__(self, **kwargs: Any) -> None:
        """
        智普大模型
        :args：自定义参数
        :param kwargs:
        """
        temperature = kwargs.pop("temperature", zhipu_constants.TEMPERATURE)
        model = kwargs.pop("model", zhipu_constants.MODEL)
        openai_api_key = kwargs.pop("openai_api_key", zhipu_constants.OPENAI_API_KEY)
        openai_api_base = kwargs.pop("openai_api_base", zhipu_constants.OPENAI_API_BASE)
        super().__init__(temperature=temperature,
                         model=model,
                         openai_api_key=openai_api_key,
                         openai_api_base=openai_api_base, **kwargs)
