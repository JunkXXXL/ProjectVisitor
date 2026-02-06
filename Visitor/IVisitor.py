from abc import ABC, abstractmethod
from pathlib import Path


class IVisitor(ABC):
    def __init__(self):
        pass

    @abstractmethod
    def visit_standard_folder(self, path_to_folder: Path):
        pass
