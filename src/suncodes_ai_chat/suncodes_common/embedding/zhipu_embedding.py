from typing import Any

from langchain_openai.embeddings.base import OpenAIEmbeddings

from suncodes_ai_chat.suncodes_constants import zhipu_constants


class ZhipuEmbeddings(OpenAIEmbeddings):
    def __init__(self, **kwargs: Any) -> None:
        """Initialize with API key."""
        super().__init__(model=zhipu_constants.EMBEDDINGS_MODEL,
                         openai_api_key=zhipu_constants.OPENAI_API_KEY,
                         openai_api_base=zhipu_constants.OPENAI_API_BASE, **kwargs)
