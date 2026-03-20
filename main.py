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
from Filler.RagFlowFiller import RagFlowFiller
from observability import get_metrics_logger, log_event, measure_time, get_cpu_load_percent

load_dotenv()


class Application:
    def __init__(self):
        self.logger = get_metrics_logger("application")
        self.folders = []
        self.visitor = PythonExportVisitor()
        with open("config.yml", 'r') as fl:
            folders = yaml.safe_load(fl)["Application"]["observe-folders"]
            for folder_path in folders:
                self.folders.append(StandardFolder(folder_path))

        OAK = os.getenv("OPEN_AI_KEY")
        el_connector = ElasticConnector(EmbedderOpenAI(OAK))
        self.filler = RagFlowFiller(el_connector)

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
            changed_files.append([changed, folder])
        return changed_files

    def load(self):
        log_event(
            self.logger,
            "user_request_received",
            request_type="project_scan",
            observed_projects=len(self.folders),
            cpu_load_percent=get_cpu_load_percent(),
        )
        processed_projects = 0
        with measure_time(
            self.logger,
            "application_runtime",
            projects_total=len(self.folders),
        ):
            modifications = self.check_modifications()
            for modified_project in modifications:
                project_name = modified_project[1]
                files_to_process = modified_project[0]
                with measure_time(
                    self.logger,
                    "project_processing_time",
                    project_name=project_name.name,
                    files_detected=len(files_to_process),
                    cpu_load_percent=get_cpu_load_percent(),
                ):
                    self.filler.add_document(project_name, files_to_process)
                processed_projects += 1
                log_event(
                    self.logger,
                    "processed_projects_total",
                    processed_projects=processed_projects,
                    project_name=project_name.name,
                )


class Context:
    def __init__(self):
        OAK = os.getenv("OPEN_AI_KEY")

        self.el_conn = ElasticConnector(EmbedderOpenAI(OAK))

    def test(self):
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
        document[0]["content_with_weight"] = "Русские перцы>?>?>>?"
        document = {"doc_id": "af176956dcb411f0b9ddba71510c7ad1",
                    "content_with_weight": "русккие перцы22"}
        document2 = {"chunk_id": "ae592ff9d044a3c2", "doc_id": "af176956dcb411f0b9ddba71510c7ad1",
                    "content_with_weight": "русккие перцы22"}
        with RagFlowConnector() as c:
            print(self.el_conn.update_chunk(c, document2))


if __name__ == '__main__':
    app = Application()
    app.load()
