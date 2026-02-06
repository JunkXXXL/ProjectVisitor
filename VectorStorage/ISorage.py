from abc import ABC, abstractmethod
from pathlib import Path



class IStorage(ABC):

    @abstractmethod
    def load_chuncks(self):
        pass