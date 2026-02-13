from pathlib import Path
import yaml
from BDconnector.BDConnector import BDConnector
import mysql.connector
from mysql.connector import errorcode
from BDconnector.ragflow.services.knowledgebase_service import KnowledgebaseService
from BDconnector.ragflow.services.file_service import FileService
from BDconnector.ragflow.services.file2document_sevice import File2DocumentService
from BDconnector.ragflow.services.document_service import DocumentService
from BDconnector.ragflow.db_ragflow import Document, Knowledgebase


class RagFlowConnector(BDConnector):
    def __init__(self):
        with open("config.yml") as fl:
            config = yaml.safe_load(fl)
        self.bd_host = config['BD']['mysql']['host']
        self.bd_port = config['BD']['mysql']['port']
        self.bd_password = config['BD']['mysql']['password']
        self.cnx = None
        self.tenant_id = "b2706914dcb311f0a16dba71510c7ad1"
        self.created_by = "b2706914dcb311f0a16dba71510c7ad1"

    def __enter__(self):
        try:
            self.cnx = mysql.connector.connect(user='root', password=self.bd_password,
                                               host=self.bd_host,
                                               port=self.bd_port,
                                               database="rag_flow")
        except mysql.connector.Error as err:
            if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
                raise mysql.connector.Error("Something is wrong with your user name or password")
            elif err.errno == errorcode.ER_BAD_DB_ERROR:
                raise mysql.connector.Error("Database does not exist")
            else:
                raise err
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cnx.close()

    def add_knowledgebase(self, knowledgebase_name: str) -> Knowledgebase:
        with self.cnx.cursor() as cursor:
            kb = KnowledgebaseService.add_knowledgebase(cursor, knowledgebase_name, self.tenant_id, self.created_by)
            file_kb_id = FileService.add_knowledgebase(cursor, knowledgebase_name, self.tenant_id, self.created_by)
            if not file_kb_id:
                raise ValueError(f"File База знаний '{knowledgebase_name}' не создана.")

            self.cnx.commit()
            return kb

    def add_document(self, document_path: Path, kb_name: str) -> str:
        with self.cnx.cursor() as cursor:
            kb = KnowledgebaseService.get_by_name(cursor, kb_name)

            if not kb:
                raise ValueError(f"База знаний '{kb_name}' не найдена.")

            file_kb = FileService.get_by_name(cursor, kb_name)
            if not file_kb:
                raise ValueError(f"File База знаний '{kb_name}' не найдена.")

            document = DocumentService.get_by_name(cursor, str(document_path), kb.id)
            if not document:
                document_id = DocumentService.add_file(cursor, document_path, kb.id, self.created_by)
            else:
                document_id = document.id
                raise FileExistsError(f"Документ {str(document_path)} уже существует в базе document")

            file = FileService.get_by_name(cursor, str(document_path))
            if not file:
                file_id = FileService.add_file(
                    cursor,
                    document_path,
                    file_kb.id,  # Читаемо и понятно
                    self.tenant_id,  # Мы сразу получили и tenant_id тоже
                    self.created_by
                )
            else:
                file_id = file.id
                raise FileExistsError(f"Документ {str(document_path)} уже существует в базе file")

            File2DocumentService.connect_knowledgebase_file(cursor, file_id, document_id)
            self.cnx.commit()
            return document_id

    def update_document(self, document_path: Path) -> None:

        with self.cnx.cursor() as cursor:
            kb = 1
            document = DocumentService.get_by_name(cursor, str(document_path), kb.id)
            if not document:
                raise FileExistsError(f"Документ {str(document_path)} не найден в системе")

            file = FileService.get_by_name(cursor, str(document_path))
            if not file:
                raise FileExistsError(f"Документ {str(document_path)} не существует")

            DocumentService.update_file(cursor, document.id)
            FileService.update_file(cursor, file.id)
            self.cnx.commit()

    def is_knowledgebase_exist(self, kb_name: str) -> (bool, None | Knowledgebase):
        with self.cnx.cursor() as cursor:
            kb = KnowledgebaseService.get_by_name(cursor, kb_name)
            if kb is None:
                return False, None
            else:
                return True, kb

    def is_document_exist(self, kb_name: str, doc_name: Path) -> (bool, None | Document):
        with self.cnx.cursor() as cursor:
            kb = KnowledgebaseService.get_by_name(cursor, kb_name)
            doc = DocumentService.get_by_name(cursor, str(doc_name), kb.id)
            if doc is None:
                return False, None
            else:
                return True, doc

