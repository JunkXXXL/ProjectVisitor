from Folder.IFolder import IFolder
from Visitor.IVisitor import IVisitor
from queue import Queue
from pathlib import Path
from typing import List
from observability import get_metrics_logger, log_event


class StandardFolder(IFolder):
    def accept(self, visitor: IVisitor) -> List:
        logger = get_metrics_logger("filesystem")
        if not self.exists():
            log_event(logger, "observed_folder_missing", folder_path=str(self.absolute()))
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
                changed_files.append(file)
        return changed_files
