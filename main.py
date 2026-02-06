from typing import List
from pathlib import Path
from Visitor import ProjectExportVisitor, PythonExportVisitor
from Folder import IFolder, StandardFolder
import yaml
from BDconnector.ragflow import RagFlowConnector


class Application:
    def __init__(self, visitor: type(ProjectExportVisitor)):
        self.folders = []
        self.visitor = visitor
        with open("config.yml", 'r') as fl:
            folders = yaml.safe_load(fl)["Application"]["observe-folders"]
            for folder_path in folders:
                self.folders.append(StandardFolder(folder_path))

    def add_folder(self, folder: IFolder):
        self.folders.append(folder)
        self._save_folder_changes()

    def _save_folder_changes(self):
        with open("config.yml", 'r') as fl:
            config = yaml.safe_load(fl)
        config["Application"]["observe-folders"] = self.folders
        with open("config.yml", 'w') as fl:
            yaml.dump(config, fl, default_flow_style=False, allow_unicode=True)

    def check_modifications(self):
        changed_files = []
        for folder in self.folders:
            changed = folder.accept(self.visitor)
            changed_files.extend(changed)
        return changed_files


if __name__ == '__main__':
    with RagFlowConnector() as c:
        c.add_knowledgebase("yadedinside")
        c.add_document(Path("abc.txt"), "yadedinside")
    exit()

    visitor = PythonExportVisitor()
    app = Application(visitor)
    print(app.check_modifications())

    strange_file = StandardFolder("D:\SibCenter\ProjectVisitor\Folder\AAO.txt")
    strange_file.write_text("HA RA SHO ")

    print(app.check_modifications())

