from BDconnector.ragflow.db_ragflow import File
from pathlib import Path
from datetime import datetime, timezone


class FileService:
    @staticmethod
    def add_file(cursor, file_path: Path, kb_id: str, tenant_id: str, user_id: str):
        """
        Создает объект File и сохраняет его в БД через переданный курсор.
        """
        # 1. Создаем экземпляр данных
        new_file = File(
            name=str(file_path),
            parent_id=kb_id,
            tenant_id=tenant_id,
            created_by=user_id,
            location=str(file_path),
            size=file_path.stat().st_size if file_path.exists() else 1,
            type="doc",
            source_type="knowledgebase"
        )

        # 2. Подготавливаем запрос
        query = """
            INSERT INTO file (
                id, create_time, create_date, update_time, update_date, parent_id, tenant_id, created_by, 
                name, location, size, type, source_type
            ) 
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """

        # 3. Формируем кортеж данных напрямую из объекта
        data = (
            new_file.id,
            new_file.create_time,
            str(new_file.create_date),
            new_file.update_time,
            str(new_file.update_date),
            new_file.parent_id,
            new_file.tenant_id,
            new_file.created_by,
            new_file.name,
            new_file.location,
            new_file.size,
            new_file.type,
            new_file.source_type
        )

        cursor.execute(query, data)
        return new_file.id

    @staticmethod
    def add_knowledgebase(cursor, name: str, tenant_id: str, created_by: str):

        knowledgebase = FileService.get_by_name(cursor, ".knowledgebase")
        if not knowledgebase:
            raise ValueError(f"Запись в file '.knowledgebase' не найдена.")
        # 1. Создаем экземпляр данных
        new_knowledgebase = File(
            name=name,
            parent_id=knowledgebase.id,
            tenant_id=tenant_id,
            created_by=created_by,
            location=None,
            size=0,
            type="folder",
            source_type="knowledgebase"
        )

        # 2. Подготавливаем запрос
        query = """
                    INSERT INTO file (
                        id, create_time, create_date, update_time, update_date, parent_id, tenant_id, created_by, 
                        name, location, size, type, source_type
                    ) 
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """

        # 3. Формируем кортеж данных напрямую из объекта
        data = (
            new_knowledgebase.id,
            new_knowledgebase.create_time,
            str(new_knowledgebase.create_date),
            new_knowledgebase.update_time,
            str(new_knowledgebase.update_date),
            new_knowledgebase.parent_id,
            new_knowledgebase.tenant_id,
            new_knowledgebase.created_by,
            new_knowledgebase.name,
            new_knowledgebase.location,
            new_knowledgebase.size,
            new_knowledgebase.type,
            new_knowledgebase.source_type
        )

        cursor.execute(query, data)
        return new_knowledgebase.id

    @staticmethod
    def get_by_name(cursor, name: str):
        query = "SELECT * FROM file WHERE name = %s"

        cursor.execute(query, (name,))

        columns = [col[0] for col in cursor.description]
        row = cursor.fetchone()

        if not row:
            return None

        row_dict = dict(zip(columns, row))
        cursor.fetchall()

        return File.from_row(row_dict)

    @staticmethod
    def update_file(cursor, document_id: str):
        current_time = datetime.now(tz=timezone.utc).timestamp()
        current_date = datetime.now(tz=timezone.utc)
        query = "UPDATE file SET update_time = %s, update_date = %s WHERE id = %s "
        data = (current_time, current_date, document_id)

        cursor.execute(query, data)
