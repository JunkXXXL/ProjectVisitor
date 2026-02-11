from ..db_ragflow import File2Document


class File2DocumentService:
    @staticmethod
    def connect_knowledgebase_file(cursor, file_id: str, document_id: str):
        file2doc = File2Document(
            file_id=file_id,
            document_id=document_id
        )

        query = """
                INSERT INTO file2document (
                    id, create_time, create_date, update_time, update_date, file_id, document_id
                ) 
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """

        data = (file2doc.id,
                file2doc.create_time,
                file2doc.create_date,
                file2doc.update_time,
                file2doc.create_date,
                file2doc.file_id,
                file2doc.document_id)
        cursor.execute(query, data)
        return file2doc.id
