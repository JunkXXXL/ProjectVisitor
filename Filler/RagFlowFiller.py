from VectorStorage.ElasticConnector import ElasticConnector
from BDconnector.ragflow.RagFlowConnector import RagFlowConnector
from Chunker.SimpleChunker import SimpleChunker
from pathlib import Path


class RagFlowFiller:
    def __init__(self, elasticConnector: ElasticConnector):
        self.el = elasticConnector
        self.chunker = SimpleChunker()

    def add_document(self, project_folder: Path, files_name: list[Path]):
        success = 0
        fail = 0

        with RagFlowConnector() as c:
            is_exist, kb = c.is_knowledgebase_exist(project_folder.name)

            if not is_exist:
                kb = c.add_knowledgebase(project_folder.name)

            for file in files_name:
                try:
                    is_exist, doc = c.is_document_exist(project_folder.name, file)
                    if is_exist:
                        index_name = "ragflow_" + kb.tenant_id
                        chunks_id = self.el.get_doc_chunks(doc.id, kb.id, index_name)
                        doc_id = doc.id
                        # удалить Все эти чанки
                        for chunk_to_delete in chunks_id:
                            self.el.delete_chunk(chunk_to_delete, index_name)

                    else:
                        print("dont exist(")
                        doc_id = c.add_document(file, project_folder.name)

                except ValueError as e:
                    print("ValueError", e)
                    fail += 1
                    continue
                except FileExistsError as e:
                    print("FileExistsError", e)
                    fail += 1
                    continue
                except Exception as e:
                    print(e)
                    fail += 1
                    continue

                chunks = self.chunker.invoke(file)

                for chunk in chunks:
                    req = {"content_with_weight": chunk,
                           "doc_id": doc_id}

                    try:
                        chunk_id = self.el.add_chuck(c, req)
                        success += 1
                    except ValueError as e:
                        print(str(e))
                        fail += 1
                    except Exception as e:
                        print(f"Exception: {e}")
                        fail += 1

        print(f"success: {success}, fails: {fail}")
