from elasticsearch import Elasticsearch, NotFoundError
from BDconnector.ragflow.services.document_service import DocumentService
from BDconnector.ragflow.services.knowledgebase_service import KnowledgebaseService
from datetime import datetime, timezone
import re
import xxhash
import yaml
import copy
import json


class ElasticConnector:
    def __init__(self, embedder):
        with open("config.yml", 'r') as fl:
            config = yaml.safe_load(fl)
            host = r"http://" + config["BD"]["elastic"]["host"] + ":" + config["BD"]["elastic"]["port"]
            basic_auth = ['user', config["BD"]["elastic"]["password"]]
        self.es = Elasticsearch(hosts=host, basic_auth=basic_auth, verify_certs=False)
        self.embedder = embedder

    def update_chunk(self, connector, req: dict):
        cursor = connector.cnx.cursor()
        d = {"id": req["chunk_id"],
            "content_with_weight": req["content_with_weight"]}
        d["content_ltks"] = req["content_with_weight"]
        d["content_sm_ltks"] = d["content_ltks"]
        if "important_kwd" in req:
            if not isinstance(req["important_kwd"], list):
                cursor.close()
                raise ValueError("`important_kwd` should be a list")
            d["important_kwd"] = req["important_kwd"]
            d["important_tks"] = req["important_kwd"]
        if "question_kwd" in req:
            if not isinstance(req["question_kwd"], list):
                cursor.close()
                raise ValueError("`question_kwd` should be a list")
            d["question_kwd"] = req["question_kwd"]
            d["question_tks"] = "\n".join(req["question_kwd"])
        if "tag_kwd" in req:
            d["tag_kwd"] = req["tag_kwd"]
        if "tag_feas" in req:
            d["tag_feas"] = req["tag_feas"]
        if "available_int" in req:
            d["available_int"] = req["available_int"]

        try:
            tenant_id = DocumentService.get_tenant_id(cursor, req["doc_id"])
            if not tenant_id:
                cursor.close()
                raise ValueError("Tenant not found!")

            embd_mdl = self.embedder

            doc = DocumentService.get_by_id(cursor, req["doc_id"])
            if doc is None:
                cursor.close()
                raise ValueError("Document not found!")

            v, c = embd_mdl.encode(doc.name + " " + req["content_with_weight"])
            v = 0.1 * v[0] + 0.9 * v[1]
            d["q_%d_vec" % len(v)] = v.tolist()
            self.update(f"ragflow_{tenant_id}", req["chunk_id"], d)
            cursor.close()
            return True
        except Exception as e:
            cursor.close()
            raise Exception(e)

    def add_chuck(self, connector, req: dict):
        cursor = connector.cnx.cursor()
        chunk_id = xxhash.xxh64((req["content_with_weight"] + req["doc_id"]).encode("utf-8")).hexdigest()
        d = {"id": chunk_id, "content_ltks": req["content_with_weight"],
             "content_with_weight": req["content_with_weight"]}
        d["content_sm_ltks"] = d["content_ltks"]
        d["important_kwd"] = req.get("important_kwd", [])
        if not isinstance(d["important_kwd"], list):
            cursor.close()
            raise ValueError("`important_kwd` is required to be a list")
        d["important_tks"] = d["important_kwd"]
        d["question_kwd"] = req.get("question_kwd", [])
        if not isinstance(d["question_kwd"], list):
            cursor.close()
            raise ValueError("`question_kwd` is required to be a list")
        d["question_tks"] = d["question_kwd"]
        d["create_time"] = str(datetime.now(tz=timezone.utc)).replace("T", " ")[:19]
        d["create_timestamp_flt"] = datetime.now(tz=timezone.utc).timestamp()
        if "tag_feas" in req:
            d["tag_feas"] = req["tag_feas"]
        if "tag_feas" in req:
            d["tag_feas"] = req["tag_feas"]

        try:
            doc = DocumentService.get_by_id(cursor, req["doc_id"])
            if doc is None:
                cursor.close()
                raise ValueError("Document not found!")
            d["kb_id"] = [doc.kb_id]
            d["docnm_kwd"] = doc.name
            d["title_tks"] = doc.name
            d["doc_id"] = doc.id

            tenant_id = DocumentService.get_tenant_id(cursor, req["doc_id"])
            if not tenant_id:
                cursor.close()
                raise ValueError("Tenant not found!")

            kb = KnowledgebaseService.get_by_id(cursor, doc.kb_id)
            if kb is None:
                cursor.close()
                raise ValueError("Knowledgebase not found!")

            embd_mdl = self.embedder

            v, c = embd_mdl.encode(doc.name + " " + req["content_with_weight"])
            v = 0.1 * v[0] + 0.9 * v[1]
            d["q_%d_vec" % len(v)] = v.tolist()
            self.insert([d], f"ragflow_{tenant_id}", doc.kb_id)

            DocumentService.increment_chunk_num(
                cursor, doc.id, doc.kb_id, c, 1)
            cursor.close()
            return chunk_id
        except Exception as e:
            cursor.close()
            print(e)
            raise e

    def check_index_exists(self, indexName: str):
        try:
            return self.es.indices.exists(index=indexName)
        except Exception as e:
            raise ConnectionError(f"Невозможно выполнить функцию check_index_exists, соединение с elastic разорвано. "
                                  f"Error: {e}")

    def insert(self, documents: list[dict], indexName: str, knowledgebaseId: str = None):
        operations = []
        for d in documents:
            d_copy = copy.deepcopy(d)
            d_copy["kb_id"] = knowledgebaseId
            meta_id = d_copy.pop("id", "")
            operations.append(
                {"index": {"_index": indexName, "_id": meta_id}})
            operations.append(d_copy)

        try:
            res = []
            r = self.es.bulk(index=indexName, operations=operations,
                             refresh=False, timeout="60s")
            if re.search(r"False", str(r["errors"]), re.IGNORECASE):
                return res

            for item in r["items"]:
                for action in ["create", "delete", "index", "update"]:
                    if action in item and "error" in item[action]:
                        res.append(str(item[action]["_id"]) + ":" + str(item[action]["error"]))
            return res

        except Exception as e:
            raise ConnectionError("ES insert got exception: " + str(e))

    def update(self, indexName: str, chunkId, newValue: dict) -> bool:
        try:
            newValue.pop("id")
            response = self.es.update(
                index=indexName,
                id=chunkId,
                body={"doc": newValue},
                refresh=True  # refresh=True делает изменения видимыми для поиска сразу
            )
            return response
        except NotFoundError:
            raise f"Документ с id {chunkId} не найден"
        except Exception as e:
            raise Exception(f"ESConnection.update(index={indexName}, id={chunkId}, doc={json.dumps(newValue, ensure_ascii=False)}) got exception")

    def delete_chunk(self, chunk_id: str, index_name: str):
        try:
            response = self.es.delete(
                index=index_name,
                id=chunk_id,
                refresh=True  # Делает удаление мгновенно видимым для поиска
            )
            return response

        except NotFoundError as e:
            # Если документа нет, выбрасываем ValueError (ошибка в логике/ID)
            raise ValueError(f"Ошибка: Документ с ID '{chunk_id}' не найден в индексе '{index_name}'.") from e

        except Exception as e:
            # Общий сбой (проблемы с сетью, авторизацией и т.д.)
            raise RuntimeError(f"Критическая ошибка при попытке удаления документа '{chunk_id}': {e}") from e

    def get_doc_chunks(self, doc_id: str, kb_id: str, index_name: str) -> list[str]:
        query = {
            "query": {
                "bool": {
                    "must": [
                        {"term": {"doc_id": doc_id}},
                        {"term": {"kb_id": kb_id}}
                    ]
                }
            }
        }

        result = self.es.search(index=index_name, body=query)
        ids = [hit['_id'] for hit in result['hits']['hits']]
        return ids
