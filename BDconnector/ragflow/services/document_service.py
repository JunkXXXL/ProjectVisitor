from BDconnector.ragflow.db_ragflow import Document
from BDconnector.ragflow.services.knowledgebase_service import KnowledgebaseService
from pathlib import Path
from datetime import datetime, timezone


class DocumentService:
    @staticmethod
    def add_file(cursor, file_name: Path, kb_id: str, user_id: str):
        # 1. Создаем экземпляр данных
        new_file = Document(
            kb_id=kb_id,
            parser_id="naive",
            parser_config=r'{"layout_recognize": "DeepDOC", "chunk_token_num": 512, "delimiter": "\n", "auto_keywords": 0, "auto_questions": 0, "html4excel": false, "topn_tags": 3, "raptor": {"use_raptor": true, "prompt": "Please summarize the following paragraphs. Be careful with the numbers, do not make things up. Paragraphs as following:\n      {cluster_content}\nThe above is the content you need to summarize.", "max_token": 256, "threshold": 0.1, "max_cluster": 64, "random_seed": 0}, "graphrag": {"use_graphrag": true, "entity_types": ["organization", "person", "geo", "event", "category"], "method": "light"}}',
            source_type="local",
            type="doc",
            created_by=user_id,
            name=str(file_name),
            location=str(file_name),
            size=1,
            token_num=1,
            chunk_num=1,
            progress=1,
            progress_msg="progress_msg",
            meta_fields='{}',
            suffix=file_name.suffix,
            run=3,
            status=1
        )

        # 2. Подготавливаем запрос
        query = """
            INSERT INTO document (
                id, create_time, create_date, update_time, update_date, kb_id, parser_id, parser_config, 
                source_type, type, created_by, name, location, size, token_num, chunk_num, progress,
                progress_msg, meta_fields, suffix, run, status, process_begin_at, process_duration
            ) 
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """

        # 3. Формируем кортеж данных напрямую из объекта
        data = (
            new_file.id,
            new_file.create_time,
            str(new_file.create_date),
            new_file.update_time,
            str(new_file.update_date),
            new_file.kb_id,
            new_file.parser_id,
            new_file.parser_config,
            new_file.source_type,
            new_file.type,
            new_file.created_by,
            new_file.name,
            new_file.location,
            new_file.size,
            new_file.token_num,
            new_file.chunk_num,
            new_file.progress,
            new_file.progress_msg,
            new_file.meta_fields,
            new_file.suffix,
            new_file.run,
            new_file.status,
            new_file.process_begin_at,
            new_file.process_duration
        )

        cursor.execute(query, data)
        return new_file.id

    @staticmethod
    def get_by_name(cursor, document_name: str, kb_id: str):
        query = "SELECT * FROM document WHERE name = %s and kb_id = %s"
        data = (document_name, kb_id)
        cursor.execute(query, data)

        columns = [col[0] for col in cursor.description]
        row = cursor.fetchone()

        if not row:
            return None

        row_dict = dict(zip(columns, row))
        cursor.fetchall()

        return Document.from_row(row_dict)

    @staticmethod
    def get_embd_id(cursor, id_: str):
        query = ("SELECT kb.embd_id FROM knowledgebase kb"
                 "JOIN document d ON kb.id = d.kb_id"
                 "WHERE d.id = %s")
        data = (id_,)
        cursor.execute(query, data)
        row = cursor.fetchone()

        if not row:
            return None
        cursor.fetchall()

        return row[0]

    @staticmethod
    def get_by_id(cursor, id_: str):
        query = "SELECT * FROM document WHERE id = %s"
        data = (id_,)
        cursor.execute(query, data)

        columns = [col[0] for col in cursor.description]
        row = cursor.fetchone()

        if not row:
            return None

        row_dict = dict(zip(columns, row))
        cursor.fetchall()

        return Document.from_row(row_dict)

    @staticmethod
    def get_tenant_id(cursor, document_id: str) -> str | None:
        query = """
                SELECT kb.tenant_id
                FROM knowledgebase kb
                JOIN document d ON kb.id = d.kb_id
                WHERE d.id = %s;
                """
        data = (document_id,)
        cursor.execute(query, data)
        row = cursor.fetchone()

        if not row:
            return None

        cursor.fetchall()

        return row[0]

    @staticmethod
    def update_file(cursor, document_id: str):
        current_time = datetime.now(tz=timezone.utc).timestamp()
        current_date = datetime.now(tz=timezone.utc)
        query = "UPDATE document SET update_time = %s, update_date = %s WHERE id = %s "
        data = (current_time, current_date, document_id)

        cursor.execute(query, data)

    @staticmethod
    def increment_chunk_num(cursor, doc_id, kb_id, token_num, chunk_num):
        document = DocumentService.get_by_id(cursor, doc_id)
        query = "UPDATE document SET token_num=%s, chunk_num=%s WHERE id=%s"
        data = (document.token_num + token_num,
                document.chunk_num + chunk_num,
                document.id)
        cursor.execute(query, data)
        KnowledgebaseService.increment_chunk_num(cursor, kb_id, token_num, chunk_num)

