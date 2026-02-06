from pathlib import Path
from Visitor.IVisitor import IVisitor
from typing import List
import yaml


class ProjectExportBase(IVisitor):
    def __init__(self):
        super().__init__()
        self.file_changes = {}
        self.doc_formats = []
        with open("config.yml", 'r') as fl:
            formats = yaml.safe_load(fl)
            self.doc_formats = formats["ExportersFormats"][self.__class__.__name__]["formats"]

    def visit_standard_folder(self, path_to_file: Path) -> bool:
        path = str(path_to_file)
        time_changes = path_to_file.stat().st_mtime
        if path_to_file.suffix in self.doc_formats:
            if path in self.file_changes:
                return self._is_file_changed(path, time_changes)
            else:
                self.file_changes |= {path: time_changes}
                return True
        return False

    def _is_file_changed(self, path, time_changes):
        if self.file_changes[path] < time_changes:
            self.file_changes[path] = time_changes
            return True
        else:
            return False


class ProjectExportVisitor(ProjectExportBase):
    def __init__(self):
        super().__init__()


class PythonExportVisitor(ProjectExportBase):
    def __init__(self):
        super().__init__()
