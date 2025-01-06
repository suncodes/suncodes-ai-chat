from typing import Any

from langchain_openai import ChatOpenAI

from suncodes_ai_chat.suncodes_constants import doubao_constants


class DouBaoAILLM(ChatOpenAI):
    """
    ZhipuAILLM: A class for interacting with the ZhipuAI API.
    """

    def __init__(self, **kwargs: Any) -> None:
        temperature = kwargs.pop("temperature", doubao_constants.TEMPERATURE)
        model = kwargs.pop("model", doubao_constants.DOUBAO_MODEL)
        openai_api_key = kwargs.pop("openai_api_key", doubao_constants.DOUBAO_API_KEY)
        openai_api_base = kwargs.pop("openai_api_base", doubao_constants.DOUBAO_BASE_URL)
        super().__init__(temperature=temperature,
                         model=model,
                         openai_api_key=openai_api_key,
                         openai_api_base=openai_api_base, **kwargs)
