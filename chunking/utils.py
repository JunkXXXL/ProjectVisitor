from typing import List
from openai import OpenAI
# import tiktoken
from sentence_transformers import SentenceTransformer
from elasticsearch import helpers
from pathlib import Path
import os
import re


BATCH_SIZE = 16

encoding = SentenceTransformer("Qwen/Qwen3-Embedding-0.6B", cache_folder="D:/huggingface/")

def get_embedding_with_usage(texts):
    # 1. Выбираем кодировщик для конкретной модели
    # Для всех новых моделей эмбеддингов OpenAI используется cl100k_base
    tokens = encoding.encode(texts, batch_size=BATCH_SIZE)
    return tokens


def clean_article_text(text: str) -> str:
    # удаление DOI
    text = re.sub(r"10\.\d{4,9}/\S+", " ", text)

    # удаление строк копирайта
    text = re.sub(r"c⃝.*?\n", " ", text)

    # удаление оглавления с точками
    text = re.sub(r"(\.\s*){2,}", " ", text)

    # удаление одиночных чисел (номера страниц)
    text = re.sub(r"\n\s*\d+\s*\n", "\n", text)

    # удаление переносов слов (abra-\nsive -> abrasive)
    text = re.sub(r"-\s*\n\s*", "", text)

    # объединение строк внутри абзаца
    text = re.sub(r"(?<!\n)\n(?!\n)", " ", text)

    # удаление лишних пробелов
    text = re.sub(r"\s+", " ", text)

    # нормализация абзацев
    text = re.sub(r"\n{2,}", "\n\n", text)

    return text.strip()


def collect_pdf_paths(root_dir_path):
    root = Path(root_dir_path)
    pdf_list = []

    # Проверяем, существует ли указанный путь
    if not root.exists() or not root.is_dir():
        print("Указанный путь не существует или не является папкой.")
        return []

    # 1. Итерируемся по содержимому корневой папки
    for folder in root.iterdir():
        # Нас интересуют только директории
        if folder.is_dir():
            # 2. Формируем путь к подпапке "current"
            current_folder = folder / "current"

            # 3. Формируем имя файла на основе имени родительской папки
            # folder.name вернет название папки, в которой мы находимся
            target_filename = f"{folder.name}.pdf"
            target_file_path = current_folder / target_filename

            # 4. Проверяем, существует ли такой файл, и добавляем в список
            if target_file_path.exists() and target_file_path.is_file():
                pdf_list.append(target_file_path)

    return pdf_list

def chunk_text(
        text: str,
        chunk_size: int = 1000,
        overlap: int = 200
) -> List[str]:
    """
    Делит текст на чанки фиксированного размера с перекрытием.
    """
    chunks = []
    start = 0
    text_length = len(text)

    while start < text_length:
        end = start + chunk_size
        chunk = text[start:end]
        chunks.append(chunk)
        start = end - overlap

    return chunks


model = OpenAI(api_key=os.getenv("OPEN_AI_KEY"))

from elasticsearch import Elasticsearch
import json


def create_index_books(es: Elasticsearch, index_name: str, dim: int = 384):
    if es.indices.exists(index=index_name):
        return

    mappings = {
        "properties": {
            "id": {
                "type": "keyword"
            },
            "file_name": {
                "type": "text"
            },
            "tags": {
                "type": "keyword"
            },
            "vector": {
                "type": "dense_vector",
                "dims": dim
            }
        }
    }

    es.indices.create(index=index_name, mappings=mappings)


def create_index_chunks(es: Elasticsearch, index_name: str, dim: int = 384):
    if es.indices.exists(index=index_name):
        return

    mappings = {
        "properties": {
            "id": {
                "type": "keyword"
            },
            "text": {
                "type": "text"
            },
            "file_name": {
                "type": "keyword"
            },
            "tags": {
                "type": "keyword"
            },
            "vector": {
                "type": "dense_vector",
                "dims": dim
            }
        }
    }
    settings = {
        "index": {
            "knn": True
        }
    }

    es.indices.create(index=index_name, mappings=mappings)


import uuid


def insert_chunk_records_bulk(
    elastic_search_conn,
    index_name: str,
    texts: list[str],
    file_name: str
):
    actions = []

    vectors = get_embedding_with_usage(texts)
    for vector, text in zip(vectors, texts):

        actions.append({
            "_index": index_name,
            "_id": str(uuid.uuid4()),
            "_source": {
                "id": str(uuid.uuid4()),
                "text": text,
                "file_name": file_name,
                "vector": vector
            }
        })

    helpers.bulk(elastic_search_conn, actions)


def insert_file_record(
    elastic_search_conn,
    index_name: str,
    text: str,
    file_name: str
):
    vector = get_embedding_with_usage([text])[0]

    doc = {
        "id": str(uuid.uuid4()),
        "file_name": file_name,
        "vector": vector
    }

    elastic_search_conn.index(
        index=index_name,
        document=doc
    )


def hybrid_search(
        es: Elasticsearch,
        index_name: str,
        query: str,
        k: int = 5
):
    query_vector = get_embedding_with_usage([query])[0]

    body = {
        "size": k,
        "query": {
            "bool": {
                "should": [
                    {
                        "match": {
                            "text": query
                        }
                    },
                    {
                        "knn": {
                            "text_vector": {
                                "vector": query_vector,
                                "k": k
                            }
                        }
                    }
                ]
            }
        }
    }

    response = es.search(index=index_name, body=body)
    return response["hits"]["hits"]

def search_files_by_vector(
    elastic_search_conn,
    index_name: str,
    query_text: str,
    top_k: int = 5
):
    query_vector = get_embedding_with_usage([query_text])[0]

    query = {
        "knn": {
            "field": "vector",
            "query_vector": query_vector,
            "k": top_k,
            "num_candidates": 50
        },
        "_source": ["file_name"]
    }

    resp = elastic_search_conn.search(
        index=index_name,
        body=query
    )

    file_names = [hit["_source"]["file_name"] for hit in resp["hits"]["hits"]]
    return file_names

def hybrid_search_chunks(
    elastic_search_conn,
    index_name: str,
    query_text: str,
    file_names: list[str],
    top_k: int = 10
):
    query_vector = get_embedding_with_usage([query_text])[0]

    query = {
        "size": top_k,
        "query": {
            "script_score": {
                "query": {
                    "bool": {
                        "must": [
                            {"match": {"text": query_text}}
                        ],
                        "filter": [
                            {"terms": {"file_name": file_names}}
                        ]
                    }
                },
                "script": {
                    "source": "cosineSimilarity(params.query_vector, 'vector') + 1.0",
                    "params": {
                        "query_vector": query_vector
                    }
                }
            }
        }
    }

    resp = elastic_search_conn.search(
        index=index_name,
        body=query
    )

    return resp["hits"]["hits"]
