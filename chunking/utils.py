from typing import List
from openai import OpenAI
# import tiktoken
from sentence_transformers import SentenceTransformer
from pathlib import Path
import os


encoding = SentenceTransformer("Qwen/Qwen3-Embedding-0.6B", cache_folder="D:/huggingface/")

def get_embedding_with_usage(texts, model="text-embedding-3-small"):
    # 1. Выбираем кодировщик для конкретной модели
    # Для всех новых моделей эмбеддингов OpenAI используется cl100k_base
    tokens = encoding.encode(texts)
    return tokens


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


def embed_text(text: List[str]) -> List[List[float]]:
    """
    Получает список строк и возвращает список эмбеддингов.
    """
    embeddings = get_embedding_with_usage(text)
    return embeddings

from elasticsearch import Elasticsearch
import json


def create_index(es: Elasticsearch, index_name: str, dim: int = 384):
    if es.indices.exists(index=index_name):
        return

    mappings = {
        "properties": {
            "text": {"type": "text"},
            "doc_id": {"type": "keyword"},
            "text_vector": {
                "type": "dense_vector",
                "dims": dim,
            }
        }
    }
    settings = {
        "index": {
            "knn": True
        }
    }

    es.indices.create(index=index_name, mappings=mappings)


from elasticsearch.helpers import bulk
import uuid


def index_chunks(
        es: Elasticsearch,
        index_name: str,
        doc_id: str,
        chunks: List[str]
):
    embeddings = []
    for chunk in chunks:
        embedded = embed_text([chunk])
        embeddings.append(embedded[0])

    actions = []
    for chunk, vector in zip(chunks, embeddings):
        action = {
            "_index": index_name,
            "_id": str(uuid.uuid4()),
            "_source": {
                "doc_id": doc_id,
                "text": chunk,
                "text_vector": vector
            }
        }
        actions.append(action)

    bulk(es, actions)


def hybrid_search(
        es: Elasticsearch,
        index_name: str,
        query: str,
        k: int = 5
):
    query_vector = embed_texts([query])[0]

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
