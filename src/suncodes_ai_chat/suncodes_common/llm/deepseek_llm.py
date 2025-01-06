"""
https://www.deepseek.com/
"""
from typing import Any

from langchain_openai import ChatOpenAI

from suncodes_ai_chat.suncodes_constants import deepseek_constants


class DeepseekAILLM(ChatOpenAI):
    """
    DeepseekAILLM: A class for interacting with the DeepseekAI API.
    """

    def __init__(self, **kwargs: Any) -> None:
        temperature = kwargs.pop("temperature", deepseek_constants.TEMPERATURE)
        model = kwargs.pop("model", deepseek_constants.DEEPSEEK_MODEL)
        openai_api_key = kwargs.pop("openai_api_key", deepseek_constants.DEEPSEEK_API_KEY)
        openai_api_base = kwargs.pop("openai_api_base", deepseek_constants.DEEPSEEK_BASE_URL)
        super().__init__(temperature=temperature,
                         model=model,
                         openai_api_key=openai_api_key,
                         openai_api_base=openai_api_base, **kwargs)
