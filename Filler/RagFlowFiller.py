from VectorStorage.ElasticConnector import ElasticConnector
from BDconnector.ragflow.RagFlowConnector import RagFlowConnector
from Chunker.SimpleChunker import SimpleChunker
from pathlib import Path
from observability import get_metrics_logger, log_event, measure_time, get_cpu_load_percent


class RagFlowFiller:
    def __init__(self, elasticConnector: ElasticConnector):
        self.el = elasticConnector
        self.chunker = SimpleChunker()
        self.logger = get_metrics_logger("processing")

    def add_document(self, project_folder: Path, files_name: list[Path]):
        success = 0
        fail = 0
        new_files_count = 0
        updated_files_count = 0
        processed_document_kb = 0.0
        project_embedding_tokens = 0

        with RagFlowConnector() as c:
            is_exist, kb = c.is_knowledgebase_exist(project_folder.name)

            if not is_exist:
                kb = c.add_knowledgebase(project_folder.name)

            for file in files_name:
                processed_document_kb += round(file.stat().st_size / 1024, 3)
                doc_exists, _ = c.is_document_exist(project_folder.name, file)
                if doc_exists:
                    updated_files_count += 1
                else:
                    new_files_count += 1

            log_event(
                self.logger,
                "project_documents_detected",
                project_name=project_folder.name,
                new_files_count=new_files_count,
                files_to_update_count=updated_files_count,
                processed_documents_kb=round(processed_document_kb, 3),
                files_total=len(files_name),
                cpu_load_percent=get_cpu_load_percent(),
            )

            for file in files_name:
                try:
                    log_event(
                        self.logger,
                        "document_processing_started",
                        project_name=project_folder.name,
                        document_path=str(file),
                        document_size_kb=round(file.stat().st_size / 1024, 3),
                    )
                    is_exist, doc = c.is_document_exist(project_folder.name, file)
                    if is_exist:
                        index_name = "ragflow_" + kb.tenant_id
                        chunks_id = self.el.get_doc_chunks(doc.id, kb.id, index_name)
                        doc_id = doc.id
                        log_event(
                            self.logger,
                            "document_existing_chunks_detected",
                            project_name=project_folder.name,
                            document_path=str(file),
                            chunk_ids=chunks_id,
                        )
                        for chunk_to_delete in chunks_id:
                            self.el.delete_chunk(chunk_to_delete, index_name)

                    else:
                        doc_id = c.add_document(file, project_folder.name)

                except ValueError as e:
                    log_event(self.logger, "document_processing_failed", project_name=project_folder.name,
                              document_path=str(file), error_type="ValueError", error=str(e))
                    fail += 1
                    continue
                except FileExistsError as e:
                    log_event(self.logger, "document_processing_failed", project_name=project_folder.name,
                              document_path=str(file), error_type="FileExistsError", error=str(e))
                    fail += 1
                    continue
                except Exception as e:
                    log_event(self.logger, "document_processing_failed", project_name=project_folder.name,
                              document_path=str(file), error_type=type(e).__name__, error=str(e))
                    fail += 1
                    continue

                with measure_time(
                    self.logger,
                    "document_processing_time",
                    project_name=project_folder.name,
                    document_path=str(file),
                ):
                    chunks = self.chunker.invoke(file)

                    for chunk in chunks:
                        req = {"content_with_weight": chunk,
                               "doc_id": doc_id,
                               "project_name": project_folder.name,
                               "document_path": str(file)}

                        try:
                            chunk_id, token_count = self.el.add_chuck(c, req)
                            project_embedding_tokens += token_count
                            log_event(
                                self.logger,
                                "document_chunk_processed",
                                project_name=project_folder.name,
                                document_path=str(file),
                                chunk_id=chunk_id,
                                embedding_tokens=token_count,
                            )
                            success += 1
                        except ValueError as e:
                            log_event(self.logger, "document_chunk_failed", project_name=project_folder.name,
                                      document_path=str(file), error_type="ValueError", error=str(e))
                            fail += 1
                        except Exception as e:
                            log_event(self.logger, "document_chunk_failed", project_name=project_folder.name,
                                      document_path=str(file), error_type=type(e).__name__, error=str(e))
                            fail += 1

        log_event(
            self.logger,
            "project_processing_summary",
            project_name=project_folder.name,
            success=success,
            fails=fail,
            new_files_count=new_files_count,
            files_to_update_count=updated_files_count,
            processed_documents_kb=round(processed_document_kb, 3),
            embedding_tokens_total=project_embedding_tokens,
            cpu_load_percent=get_cpu_load_percent(),
        )
