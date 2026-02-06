from abc import ABC, abstractmethod
from Visitor.IVisitor import IVisitor
from pathlib import Path


class IFolder(type(Path())):
    @abstractmethod
    def accept(self, visitor: IVisitor):
        pass
