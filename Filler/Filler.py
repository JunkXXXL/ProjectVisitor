


class Filler:
    def __init__(self, bdconn, el_pipeline):
        self.bdconn = bdconn
        self.el_pipeline = el_pipeline

    def add_document(self, project_folder, file_name):
        dataset_id = self.bdconn.load(project_folder, file_name)
        self.el_pipeline.load(dataset_id, file_name)
