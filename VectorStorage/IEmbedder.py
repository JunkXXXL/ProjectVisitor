from langchain_openai import OpenAIEmbeddings
from abc import ABC, abstractmethod
from langchain_community.callbacks import get_openai_callback
from numpy import array


class IEmbedder(ABC):
    @abstractmethod
    def encode(self, text: str) -> [list[float], int]:
        pass


class EmbedderOpenAI(IEmbedder):
    def __init__(self, api_key: str, model: str = "text-embedding-3-small"):
        self.client = OpenAIEmbeddings(
            api_key=api_key,
            model=model
        )

    def encode(self, text: str) -> [list[float], int]:
        # text: [заголовок, основной текст]
        with get_openai_callback() as cb:
            embedding_headline = self.client.embed_query(text[0])
            embedding_text = self.client.embed_query(text[1])
            return array([embedding_headline, embedding_text]), cb.total_tokens

# Пример использования:
# embedder = Embedder(
#     api_key="sk-...",
#     langfuse_public_key="pk-lf-...",
#     langfuse_secret_key="sk-lf-..."
# )
# vector = embedder.encode("Пример текста для LangChain")

