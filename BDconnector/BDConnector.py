from abc import ABC, abstractmethod
from pathlib import Path


class BDConnector(ABC):
    @abstractmethod
    def __enter__(self):
        pass
    @abstractmethod
    def __exit__(self, exc_type, exc_val, exc_tb):
        pass
    @abstractmethod
    def add_knowledgebase(self, knowledgebase_name: str):
        pass
    @abstractmethod
    def add_document(self, document_path: Path, kb_name: str):
        pass
