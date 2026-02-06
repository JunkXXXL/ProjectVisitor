import uuid
from dataclasses import dataclass, field, fields
from datetime import datetime, date, timezone
from typing import Optional


def uuid_hex() -> str:
    return uuid.uuid4().hex


@dataclass
class Base:
    create_time: Optional[int] = field(default_factory=lambda: int(datetime.now(tz=timezone.utc).timestamp()))
    create_date: Optional[date] = field(default_factory=lambda: datetime.now(tz=timezone.utc).date())
    update_time: Optional[int] = field(default_factory=lambda: int(datetime.now(tz=timezone.utc).timestamp()))
    update_date: Optional[date] = field(default_factory=lambda: datetime.now(tz=timezone.utc).date())

    @classmethod
    def from_row(cls, row_dict):
        """Создает объект из словаря (результата запроса)"""
        if not row_dict:
            return None

        # Фильтруем ключи словаря, чтобы они совпадали с полями dataclass
        class_fields = {f.name for f in fields(cls)}
        filtered_dict = {k: v for k, v in row_dict.items() if k in class_fields}

        return cls(**filtered_dict)


@dataclass
class Document(Base):
    id: str = field(default_factory=uuid_hex)
    thumbnail: Optional[str] = None  # base64
    kb_id: Optional[str] = None
    parser_id: Optional[str] = None
    parser_config: Optional[str] = None
    source_type: Optional[str] = None
    type: Optional[str] = None  # file extension
    created_by: Optional[str] = None
    name: Optional[str] = None
    location: Optional[str] = None
    size: Optional[int] = None
    token_num: Optional[int] = None
    chunk_num: Optional[int] = None
    progress: Optional[float] = None
    progress_msg: Optional[str] = None
    process_begin_at: Optional[date] = field(default_factory=lambda: datetime.now(tz=timezone.utc).date())
    process_duration: Optional[float] = field(default=0.)
    meta_fields: Optional[str] = None
    suffix: Optional[str] = None
    run: Optional[int] = None  # 1: run, 2: cancel
    status: Optional[int] = None  # 0: wasted, 1: valid


@dataclass
class File(Base):
    id: str = field(default_factory=uuid_hex)
    parent_id: Optional[str] = None
    tenant_id: Optional[str] = None
    created_by: Optional[str] = None
    name: Optional[str] = None
    location: Optional[str] = None
    size: Optional[int] = None
    type: Optional[str] = None
    source_type: Optional[str] = None


@dataclass
class File2Document(Base):
    id: str = field(default_factory=uuid_hex)
    file_id: Optional[str] = None
    document_id: Optional[str] = None


@dataclass
class Knowledgebase(Base):
    id: str = field(default_factory=uuid_hex)
    avatar: Optional[str] = None
    tenant_id: Optional[str] = None
    name: Optional[str] = None
    language: Optional[str] = None  # English | Chinese
    description: Optional[str] = None

    embd_id: str = "English"
    permission: str = "me"  # me | team

    created_by: Optional[str] = None
    doc_num: Optional[int] = None
    token_num: Optional[int] = None
    chunk_num: Optional[int] = None

    similarity_threshold: float = 0.2
    vector_similarity_weight: float = 0.3

    parser_id: Optional[str] = None
    parser_config: str = field(default=r'{"pages": [[1, 1000000]]}')
    pagerank: Optional[int] = None
    status: Optional[int] = None  # 0: wasted, 1: valid
