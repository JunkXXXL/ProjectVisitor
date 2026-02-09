from BDconnector.ragflow.db_ragflow import Knowledgebase
from datetime import datetime, timezone


class KnowledgebaseService:
    @staticmethod
    def add_knowledgebase(cursor, knowledgebase_name: str, tenant_id: str, user_id: str):
        """
        Создает объект Knowledgebase и сохраняет его в БД через переданный курсор.
        """

        # 1. Создаем экземпляр данных
        new_kb = Knowledgebase(
            name=knowledgebase_name,
            tenant_id=tenant_id,
            created_by=user_id,
            language="English",
            embd_id="text-embedding-3-small@OpenAI",
            permission="me",
            doc_num=1,
            token_num=1,
            chunk_num=0,
            similarity_threshold=0.2,
            vector_similarity_weight=0.3,
            parser_id="naive",
            parser_config=r'{"layout_recognize": "DeepDOC", "chunk_token_num": 512, "delimiter": "\n", "auto_keywords": 0, "auto_questions": 0, "html4excel": false, "topn_tags": 3, "raptor": {"use_raptor": true, "prompt": "Please summarize the following paragraphs. Be careful with the numbers, do not make things up. Paragraphs as following:\n      {cluster_content}\nThe above is the content you need to summarize.", "max_token": 256, "threshold": 0.1, "max_cluster": 64, "random_seed": 0}, "graphrag": {"use_graphrag": true, "entity_types": ["organization", "person", "geo", "event", "category"], "method": "light"}}',
            pagerank=0,
            status=1
        )

        # 2. Подготавливаем SQL-запрос
        query = """
            INSERT INTO knowledgebase (
                id, create_time, create_date, update_time, update_date,
                tenant_id, name, language, embd_id, permission, created_by,
                doc_num, token_num, chunk_num,
                similarity_threshold, vector_similarity_weight,
                parser_id, parser_config, pagerank, status
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """

        # 3. Формируем данные из объекта
        data = (
            new_kb.id,
            new_kb.create_time,
            new_kb.create_date,
            new_kb.update_time,
            new_kb.update_date,
            new_kb.tenant_id,
            new_kb.name,
            new_kb.language,
            new_kb.embd_id,
            new_kb.permission,
            new_kb.created_by,
            new_kb.doc_num,
            new_kb.token_num,
            new_kb.chunk_num,
            new_kb.similarity_threshold,
            new_kb.vector_similarity_weight,
            new_kb.parser_id,
            new_kb.parser_config,
            new_kb.pagerank,
            new_kb.status
        )

        cursor.execute(query, data)
        return new_kb.id

    @staticmethod
    def get_by_id(cursor, id_: str):
        query = "SELECT * FROM knowledgebase WHERE id = %s"
        cursor.execute(query, (id_,))
        columns = [col[0] for col in cursor.description]
        row = cursor.fetchone()

        if not row:
            return None

        row_dict = dict(zip(columns, row))

        return Knowledgebase.from_row(row_dict)

    @staticmethod
    def get_by_name(cursor, name: str) -> "Knowledgebase | None":
        query = "SELECT * FROM knowledgebase WHERE name = %s"

        cursor.execute(query, (name,))

        columns = [col[0] for col in cursor.description]
        row = cursor.fetchone()

        if not row:
            return None

        row_dict = dict(zip(columns, row))
        cursor.fetchall()

        return Knowledgebase.from_row(row_dict)

    @staticmethod
    def increment_chunk_num(cursor, kb_id, token_num, chunk_num):
        kb = KnowledgebaseService.get_by_id(cursor, kb_id)
        query = "UPDATE document SET token_num=%s chunk_num=%s WHERE id=%s"
        data = (kb.token_num + token_num,
                kb.chunk_num + chunk_num,
                kb.id)

        cursor.execute(query, data)


