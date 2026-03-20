from langchain_openai import OpenAIEmbeddings
from abc import ABC, abstractmethod
from langchain_community.callbacks import get_openai_callback
from numpy import array
from observability import get_metrics_logger, log_event, measure_time


class IEmbedder(ABC):
    @abstractmethod
    def encode(self, text: str, metadata: dict | None = None) -> [list[float], int]:
        pass


class EmbedderOpenAI(IEmbedder):
    def __init__(self, api_key: str, model: str = "text-embedding-3-small"):
        self.client = OpenAIEmbeddings(
            api_key=api_key,
            model=model
        )
        self.logger = get_metrics_logger("embedding")
        self.model = model

    def encode(self, text: str, metadata: dict | None = None) -> [list[float], int]:
        metadata = metadata or {}
        with get_openai_callback() as cb:
            with measure_time(self.logger, "embedding_model_response_time", model=self.model, **metadata):
                embedding_headline = self.client.embed_query(text[0])
                embedding_text = self.client.embed_query(text[1])
            log_event(self.logger, "embedding_tokens_used", model=self.model, total_tokens=cb.total_tokens, **metadata)
            return array([embedding_headline, embedding_text]), cb.total_tokens
