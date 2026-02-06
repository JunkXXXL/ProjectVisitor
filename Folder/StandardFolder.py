from Folder.IFolder import IFolder
from Visitor.IVisitor import IVisitor
from queue import Queue
from pathlib import Path
from typing import List


class StandardFolder(IFolder):
    def accept(self, visitor: IVisitor) -> List:
        if not self.exists():
            print(f"пути {str(self.absolute())} не существует")
            return []

        queue_folders = Queue()
        queue_files = Queue()
        queue_folders.put(self)

        while not queue_folders.empty():
            folder: Path = queue_folders.get()
            for element in folder.iterdir():
                if element.is_dir() and element.stem[0] != ".":
                    queue_folders.put(element)
                elif element.is_file():
                    queue_files.put(element)

        changed_files = []
        while not queue_files.empty():
            file: Path = queue_files.get()
            is_changed = visitor.visit_standard_folder(file)
            if is_changed:
                changed_files.append(str(file))
        return changed_files

