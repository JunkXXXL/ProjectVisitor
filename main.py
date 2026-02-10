from typing import List
from pathlib import Path
from Visitor import ProjectExportVisitor, PythonExportVisitor
from Folder import IFolder, StandardFolder
import yaml
from BDconnector.ragflow import RagFlowConnector
from VectorStorage.ElasticConnector import ElasticConnector
from VectorStorage.IEmbedder import EmbedderOpenAI
from datetime import datetime, timezone
from dotenv import load_dotenv
import os

load_dotenv()

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


class Context:
    def __init__(self):
        OAK = os.getenv("OPEN_AI_KEY")
        self.el_conn = ElasticConnector(EmbedderOpenAI(OAK))

    def test(self):
        #print("check_index_exists:", self.el_conn.check_index_exists("ragflow_b2706914dcb311f0a16dba71510c7ad1"))
        document = [{
            "id": 1, "content_ltks": "Русские перцы",
            "content_with_weight": "Русские перцы",
            "content_sm_ltks": "Русские перцы",
            "create_time": str(datetime.now(tz=timezone.utc)).replace("T", " ")[:19],
            "create_timestamp_flt": datetime.now(tz=timezone.utc).timestamp(),
            "kb_id": "4cad705c1c4546b883a7e37656aab5be",
            "docnm_kwd": "первый класс.txt",
            "title_tks": "Первый класс.txt",
            "doc_id": "4b25f863dcd244d089729df753075e60",
            "q_1536_vec": [0.5]*1536
        }]
        #print(self.el_conn.insert(document, "ragflow_b2706914dcb311f0a16dba71510c7ad1", "4cad705c1c4546b883a7e37656aab5be"))
        document[0]["content_with_weight"] = "Русские перцы>?>?>>?"
        #print(self.el_conn.update(1, document[0], "ragflow_b2706914dcb311f0a16dba71510c7ad1"))
        #print(self.el_conn.delete_document(1, "ragflow_b2706914dcb311f0a16dba71510c7ad1"))
        document = {"doc_id": "af176956dcb411f0b9ddba71510c7ad1",
                    "content_with_weight": "русккие перцы22"}
        document2 = {"chunk_id": "ae592ff9d044a3c2", "doc_id": "af176956dcb411f0b9ddba71510c7ad1",
                    "content_with_weight": "русккие перцы22"}
        with RagFlowConnector() as c:
            #print(self.el_conn.add_chuck(c, document))
            print(self.el_conn.update_chunk(c, document2))


if __name__ == '__main__':
    c = Context()
    c.test()

    exit()
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

